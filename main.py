# agent.py
# -----------------------------------------------------------------------------
# Agri Advisor – Hybrid RAG with grounded answers
# - Hybrid retrieval: BM25 + dense (SentenceTransformers) + RRF + CrossEncoder re-rank
# - Metadata filters: state + month (+year) + metric prefilter
# - Evidence table: LLM answers constrained to retrieved snippets, with inline sources
# - Clarification: asks ONE follow-up if critical info is missing
# - CLI loop for quick testing
#
# Setup
#   pip install -U sentence-transformers rank-bm25 faiss-cpu google-genai python-dotenv
#   # (If faiss-cpu fails on Windows: pip install faiss-cpu==1.7.4)
#
# Env
#   echo "GEMINI_API_KEY=YOUR_KEY" > .env
#
# Data folder & schema (one JSON per line)
#   {
#     "text": "State: West Bengal. Year: 2022. Month: May. Crop: rice. Wholesale Price: ₹3000/qtl. Temperature: 0.4 °C. Rainfall: 327.5 mm.",
#     "source": "Wholesale.xlsx[sheet=Sheet1]#STATE=West Bengal/row1012",
#     "state": "west bengal",
#     "crop": "rice",
#     "year": 2022,
#     "months": ["May"],
#     "metric": "price_weather"  # optional but recommended: rainfall|price|price_weather|pop|policy|finance|news
#   }
# -----------------------------------------------------------------------------

import os
import re
import json
import time
import numpy as np
import faiss
from typing import List, Dict, Any, Tuple
from glob import glob

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
from google import genai  # google-genai SDK

# ---------- Data location ----------
DATA_DIR = "./data"
# load ALL jsonl shards (e.g., data_v4__*.jsonl, data_v5__*.jsonl, etc.)
DATA_GLOBS = ["*.jsonl"]

# ---------- Config ----------
EMB_MODEL = "all-MiniLM-L6-v2"
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
GEMINI_MODEL = "gemini-2.5-flash-lite"
MAX_CTX_SNIPPETS = 6        # how many evidence snippets to send to the LLM
EVIDENCE_MIN = 2            # require at least this many for a grounded answer
RRF_K = 60                  # RRF constant
TOP_K_FUSION = 50           # candidates from fusion to send to reranker
RERANK_KEEP = 12            # keep these many final candidates as evidence pool

# ---------- Env & Gemini ----------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("Set GEMINI_API_KEY in your .env or shell!")
gemini = genai.Client(api_key=GEMINI_API_KEY)

# ---------- Utilities ----------
MONTHS_MAP = {
    "january":"Jan","jan":"Jan",
    "february":"Feb","feb":"Feb",
    "march":"Mar","mar":"Mar",
    "april":"Apr","apr":"Apr",
    "may":"May","may":"May",
    "june":"Jun","jun":"Jun",
    "july":"Jul","jul":"Jul",
    "august":"Aug","aug":"Aug",
    "september":"Sep","sep":"Sep",
    "october":"Oct","oct":"Oct",
    "november":"Nov","nov":"Nov",
    "december":"Dec","dec":"Dec"
}

INDIA_STATES = {
    "punjab","haryana","rajasthan","uttar pradesh","uttarakhand","himachal pradesh",
    "jammu and kashmir","ladakh","bihar","jharkhand","west bengal","odisha",
    "chhattisgarh","madhya pradesh","maharashtra","telangana","andhra pradesh",
    "tamil nadu","kerala","karnataka","gujarat","assam","tripura","meghalaya",
    "manipur","mizoram","arunachal pradesh","nagaland","sikkim","goa",
    "andaman and nicobar islands","puducherry","delhi","chandigarh",
    "lakshadweep","daman and diu","dadra and nagar haveli"
}

# crop synonyms to improve matching/intent
CROP_SYNONYMS = {
    "sorghum": ["jowar"],
    "pearl millet": ["bajra"],
    "pigeonpea": ["arhar", "tur", "toor"],
    "black gram": ["urad"],
    "green gram": ["moong"],
    "sesame": ["til"],
    "cotton": ["kapas"],
    "maize": ["corn"],
}

# --- Known crops from data (built after docs load, but declare here) ---
KNOWN_CROPS: set[str] = set()

# --- Session memory for slot filling across turns ---
_LAST_SIGNALS: Dict[str, Any] | None = None

def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9\s]", " ", s.lower())

def _has_phrase(haystack: str, phrase: str) -> bool:
    return re.search(rf"\b{re.escape(phrase)}\b", haystack) is not None

def find_crop(q: str) -> str | None:
    qn = _norm(q)

    # try known crops (multi-word first)
    known = sorted(list(KNOWN_CROPS), key=len, reverse=True)
    for c in known:
        if c and _has_phrase(qn, c):
            return c

    # synonyms → canonical
    for canon, syns in CROP_SYNONYMS.items():
        if _has_phrase(qn, canon):
            return canon
        for s in syns:
            if _has_phrase(qn, s):
                return canon
    return None


def expand_with_synonyms(q: str) -> str:
    ql = q.lower()
    extra = []
    for canon, syns in CROP_SYNONYMS.items():
        for s in syns:
            if s in ql and canon not in ql:
                extra.append(canon)
        if canon in ql:
            extra.extend([s for s in syns if s not in ql])
    return q if not extra else f"{q} ({', '.join(set(extra))})"

def find_state(q: str) -> str | None:
    ql = q.lower()
    for s in INDIA_STATES:
        if s in ql:
            return s
    return None

def find_month(q: str) -> str | None:
    ql = q.lower()
    month_names = "january|february|march|april|may|june|july|august|september|october|november|december"
    m = re.search(rf"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|{month_names})\b", ql)
    return MONTHS_MAP[m.group(0)] if m else None

def find_year(q: str) -> int | None:
    m = re.search(r"\b(19|20)\d{2}\b", q)
    return int(m.group(0)) if m else None

def detect_intent(q: str) -> str:
    ql = q.lower()
    if any(w in ql for w in ["when should i plant", "when to plant", "sowing time", "sow window", "plant in"]):
        return "sowing_window"
    if any(w in ql for w in ["variety", "seed variety", "hybrid", "cv"]):
        return "variety"
    if any(w in ql for w in ["rain", "rainfall", "monsoon", "imd", "departure"]):
        return "rainfall"
    if any(w in ql for w in ["price", "mandi", "sell", "market", "wholesale"]):
        return "market"
    if any(w in ql for w in ["fertilizer", "dose", "seed rate", "irrigat"]):
        return "pop_practice"
    if any(w in ql for w in ["yield", "production", "area", "acreage", "fertilizer", "pesticide"]):
        return "stats"
    if any(w in ql for w in ["which crop", "what crop", "suitable crop", "recommend crop", "npk", "nitrogen", "phosphorus", "potash", "ph ", " pH", "temperature", "humidity", "rainfall"]):
        return "crop_env"
    if any(w in ql for w in [
        "scheme", "yojana", "subsidy", "grant", "benefit", "eligibility",
        "apply", "application", "documents", "loan", "credit", "pension",
        "stipend", "scholarship", "assistance"
    ]):
        return "scheme"
    if any(w in ql for w in ["price", "mandi", "sell", "market"]):
        return "market"
    return "general"

def find_year(q: str) -> int | None:
    m = re.search(r"\b(19|20)\d{2}\b", q)
    return int(m.group(0)) if m else None

# globals
KNOWN_DISTRICTS: set[str] = set()
STATE_SYNONYMS = {
    "bengal": "west bengal",
    "orissa": "odisha",
    "up": "uttar pradesh",
    "mp": "madhya pradesh",
    "tn": "tamil nadu",
    "ap": "andhra pradesh",
    "hp": "himachal pradesh",
    "jk": "jammu and kashmir",
}

# after building meta:
KNOWN_DISTRICTS.update({m["district"] for m in meta if m.get("district")})

def find_state(q: str) -> str | None:
    qn = _norm(q)
    for k, v in STATE_SYNONYMS.items():
        if _has_phrase(qn, k):
            return v
    for s in INDIA_STATES:
        if _has_phrase(qn, s):
            return s
    return None

def find_district(q: str) -> str | None:
    qn = _norm(q)
    for d in KNOWN_DISTRICTS:
        if d and _has_phrase(qn, d):
            return d
    return None

# and include it in parse_query():
def parse_query(q: str) -> Dict[str, Any]:
    q_exp = expand_with_synonyms(q)
    return {
        "intent": detect_intent(q_exp),
        "state": find_state(q_exp),
        "district": find_district(q_exp),     # <— add this
        "month": find_month(q_exp),
        "year": find_year(q_exp),
        "crop": find_crop(q_exp),
        "raw": q_exp,
    }


def _merge_signals(prev: Dict[str,Any] | None, new: Dict[str,Any]) -> Dict[str,Any]:
    if not prev:
        return new
    merged = dict(prev)
    for k, v in new.items():
        if v not in (None, "", []):
            merged[k] = v
    return merged

def merged_parse_query(q: str) -> Dict[str, Any]:
    global _LAST_SIGNALS
    fresh = parse_query(q)
    cur = _merge_signals(_LAST_SIGNALS, fresh)

    # if user asked a market/price question without naming a crop, don't reuse old crop
    if fresh.get("intent") == "market" and not fresh.get("crop"):
        cur["crop"] = None

    _LAST_SIGNALS = cur.copy()
    return cur

CROP_SYNONYMS.update({
    "potato": ["aloo", "batata"],
    "onion": ["pyaz", "kanda"],
    "carrot": ["gajar"],
})

# ---------- Load docs ----------
docs: List[Dict[str, Any]] = []
files: List[str] = []
for pat in DATA_GLOBS:
    files.extend(sorted(glob(os.path.join(DATA_DIR, pat))))
if not files:
    raise RuntimeError(f"No JSONL files found in {DATA_DIR} (patterns: {DATA_GLOBS})")

for path in files:
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    docs.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        pass

if not docs:
    raise RuntimeError("No documents loaded. Put your .jsonl chunks in ./data/")
print(f"Loaded {len(docs)} documents from {len(files)} files.")

# ---------- Build corpus arrays ----------
texts = [d.get("text", "") for d in docs]
meta = [{
    "source": d.get("source", "unknown"),
    "state": (d.get("state") or "").lower() or None,
    "district": (d.get("district") or "").lower() or None,
    "crop": (d.get("crop") or "").lower() or None,
    "season": (d.get("season") or "").lower() or None,
    "months": (d.get("months") if isinstance(d.get("months"), list)
               else ([d.get("months")] if d.get("months") else None)),
} for d in docs]

# Collect crops present in data (lowercased)
KNOWN_CROPS.update({m["crop"] for m in meta if m.get("crop")})

# ---------- Build indices ----------
print("Building embeddings…")
embedder = SentenceTransformer(EMB_MODEL)
emb = embedder.encode(texts, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=True)
dim = emb.shape[1]

index = faiss.IndexFlatIP(dim)
index.add(emb.astype("float32"))

print("Building BM25…")
tokenized_corpus = [t.split() for t in texts]
bm25 = BM25Okapi(tokenized_corpus)

print("Loading cross-encoder…")
reranker = CrossEncoder(RERANK_MODEL)

# ---------- Retrieval ----------
def rrf_fuse(bm_ranked: List[int], dense_ranked: List[int], k: int = RRF_K) -> List[int]:
    scores: Dict[int, float] = {}
    for r, i in enumerate(bm_ranked):
        scores[i] = scores.get(i, 0.0) + 1.0 / (k + r + 1)
    for r, i in enumerate(dense_ranked):
        scores[i] = scores.get(i, 0.0) + 1.0 / (k + r + 1)
    fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [i for i, _ in fused]

def filter_pool(signals: Dict[str, Any]) -> List[int]:
    pool = list(range(len(docs)))

    # Deprioritize news by default
    non_news = [i for i in pool if docs[i].get("metric") != "news"]
    pool = non_news or pool

    # Intent → metric prefilter (soft)
    intent = signals.get("intent")
    if intent == "rainfall":
        rain_pool = [i for i in pool if docs[i].get("metric") == "rainfall"]
        pool = rain_pool or pool
    elif intent == "pop_practice":
        pop_pool = [i for i in pool if docs[i].get("metric") == "pop"]
        pool = pop_pool or pool
    elif intent == "stats":
        stats_pool = [i for i in pool if docs[i].get("metric") == "crop_stats"]
        pool = stats_pool or pool
    elif intent == "crop_env":
        env_pool = [i for i in pool if docs[i].get("metric") == "crop_env"]
        pool = env_pool or pool
    elif intent == "scheme":
        pool2 = [i for i in pool if docs[i].get("metric") == "scheme"]
        # optional: filter by 'level' if user asked "central" or "state"
        ql = signals["raw"].lower()
        if "central" in ql:
            pool2 = [i for i in pool2 if (docs[i].get("level") == "central")]
        if "state" in ql and signals["state"]:
            pool2 = [i for i in pool2 if (docs[i].get("level") == "state" and (docs[i].get("state") == signals["state"]))]
        pool = pool2 or pool
    elif intent == "market":
        pool2 = [i for i in pool if docs[i].get("metric") in ("price", "price_weather", "market")]
        if signals.get("district"):
            d = signals["district"]
            pool2 = [i for i in pool2 if meta[i]["district"] == d]
        if signals.get("state"):
            s = signals["state"]
            pool2 = [i for i in pool2 if meta[i]["state"] == s]
        if signals.get("year"):
            y = signals["year"]
            pool2 = [i for i in pool2 if docs[i].get("year") == y]
        pool = pool2 or pool


    # Year preference (soft)
    if signals.get("year") is not None:
        y = signals["year"]
        y_pool = [i for i in pool if docs[i].get("year") == y]
        pool = y_pool or pool

    # State filter with rainfall fallback to all-India
    if signals.get("state"):
        s = signals["state"]
        by_state = [i for i in pool if meta[i]["state"] == s]
        if by_state:
            pool = by_state
        elif intent == "rainfall":
            ai = [i for i in pool if (docs[i].get("region") == "all-india")]
            pool = ai or pool

    # Crop filter (hard when we know the crop)
    if signals.get("crop"):
        c = signals["crop"]
        crop_pool = [i for i in pool if meta[i]["crop"] == c]
        pool = crop_pool or pool

    # Month filter
    if signals.get("month"):
        mo = signals["month"]
        by_month = [i for i in pool if meta[i]["months"] and mo in meta[i]["months"]]
        pool = by_month or pool

    return pool

def hybrid_search(q: str, k_fusion: int = TOP_K_FUSION, k_rerank: int = RERANK_KEEP) -> Tuple[Dict[str, Any], List[int]]:
    signals = merged_parse_query(q)
    pool = filter_pool(signals)
    if not pool:
        pool = list(range(len(docs)))

    # BM25 over full then select pool by top scores
    bm_scores = bm25.get_scores(q.split())
    bm_pairs = [(i, bm_scores[i]) for i in pool]
    bm_ranked = [i for i, _ in sorted(bm_pairs, key=lambda x: x[1], reverse=True)[:k_fusion]]

    # Dense over full then filter to pool
    qv = embedder.encode([q], normalize_embeddings=True, convert_to_numpy=True)
    _, I = index.search(qv.astype("float32"), min(k_fusion*2, len(docs)))
    dense_filtered = [i for i in I[0] if i in pool][:k_fusion]

    # RRF fusion
    fused = rrf_fuse(bm_ranked, dense_filtered)
    fused = fused[:max(k_fusion, k_rerank)]

    # Cross-encoder rerank
    pairs = [[q, texts[i]] for i in fused]
    if not pairs:
        return signals, []
    rr_scores = reranker.predict(pairs)
    reranked = [i for i, _ in sorted(zip(fused, rr_scores), key=lambda x: x[1], reverse=True)]
    return signals, reranked[:k_rerank]

# ---------- Prompting ----------
def make_evidence(idxs: List[int], limit: int = MAX_CTX_SNIPPETS) -> List[Dict[str, str]]:
    ev = []
    seen = set()
    for i in idxs[:limit]:
        snip = texts[i].strip().replace("\n", " ")
        src = meta[i]["source"] or "unknown"
        key = (snip[:100], src)
        if key in seen:
            continue
        seen.add(key)
        ev.append({"snippet": snip[:800], "source": src})
    return ev

def build_prompt(evidence: List[Dict[str,str]], user_query: str, signals: Dict[str,Any]) -> str:
    ctx = "\n---\n".join([f"{e['snippet']}\n(Source: {e['source']})" for e in evidence])
    focus = []
    if signals.get("crop"):  focus.append(f"Crop: {signals['crop']}")
    if signals.get("state"): focus.append(f"State: {signals['state']}")
    if signals.get("month"): focus.append(f"Month: {signals['month']}")
    if signals.get("year"):  focus.append(f"Year: {signals['year']}")
    focus_line = ("Focus → " + ", ".join(focus)) if focus else "Focus only on the user's query."

    return f"""You are an agriculture assistant for Indian farmers.

        POLICY
        - {focus_line}. If EVIDENCE does not match this focus (especially the crop), ask ONE clarifying question and stop.
        - Answer ONLY using EVIDENCE below; cite sources inline (title/section/page if present).
        - Do NOT assume the current date/month. Mention months/years only if they appear in the USER QUESTION or EVIDENCE.
        - Do NOT include market prices unless the user asks about price/market.
        - Be concise and actionable: sowing window, varieties, seed rate, key cautions, next step.

        EVIDENCE
        {ctx}

        USER QUESTION
        {user_query}

        Now produce:
        1) A brief recommendation tailored to the focus above
        2) Bullet points with specifics (dates, varieties, seed rates, etc.)
        3) A 'Sources' list with the sources used
    """

def grounded_answer(q: str) -> str:
    signals, idxs = hybrid_search(q)

    # Ask for missing critical info for sowing intent
    if signals["intent"] == "sowing_window" and (signals["state"] is None or signals["month"] is None):
        missing = []
        if signals["state"] is None: missing.append("state")
        if signals["month"] is None: missing.append("month")
        ask = " and ".join(missing)
        return f"I need your {ask} to be precise. For example: 'What should I plant in May in Punjab (irrigated or rainfed?)'."

    evidence = make_evidence(idxs)
    if len(evidence) < EVIDENCE_MIN:
        return ("⚠️ This answer is not grounded in the retrieved data. Please verify independently.\n"
                "I need your district and whether you are irrigated/rainfed to answer precisely. "
                "Try: 'What should I plant in May in Punjab, irrigated, for fodder?'")

    def _majority_crop(idxs: List[int]) -> str | None:
        counts = {}
        for i in idxs[:10]:
            c = meta[i]["crop"]
            if c:
                counts[c] = counts.get(c, 0) + 1
        if not counts: return None
        return max(counts, key=counts.get)

    maj = _majority_crop(idxs)
    if signals.get("crop") and maj and maj != signals["crop"]:
        return (f"I found evidence mainly for **{maj}**, but you seem to be asking about **{signals['crop']}**. "
                f"Do you want info on {signals['crop']} or {maj}?")

    prompt = build_prompt(evidence, q, signals)
    try:
        resp = gemini.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        text = (resp.text or "").strip()
    except Exception as e:
        text = f"(Model error: {e})\n\nHere are relevant sources:\n" + \
               "\n".join(f"- {e['source']}" for e in evidence)

    # Always append a clean 'Sources' section (idempotent if model already did)
    srcs = "\n".join([f"- {e['source']}" for e in evidence])
    if "Sources" not in text:
        text += "\n\nSources:\n" + srcs
    return text

# ---------- Public API ----------
def generate_answer(user_query: str) -> str:
    return grounded_answer(user_query)

# ---------- CLI ----------
if __name__ == "__main__":
    print("🌾  Agri Advisor (grounded). Ask your question (Ctrl+C to quit).")
    try:
        while True:
            q = input("\n🟢 You: ").strip()
            if not q:
                continue
            t0 = time.time()
            ans = generate_answer(q)
            dt = time.time() - t0
            print("\n🧠 Agent:\n" + ans)
            print(f"\n⏱️  Took {dt:.2f}s")
    except KeyboardInterrupt:
        print("\n👋 Exiting.")
