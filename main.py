# agent.py
# -----------------------------------------------------------------------------
# Agri Advisor (Punjab-first) – Hybrid RAG with grounded answers
#
# What you get:
# - Hybrid retrieval: BM25 + dense (SentenceTransformers) + RRF + CrossEncoder re-rank
# - Metadata filters: state + month prefilter for precision (e.g., "Punjab May plant")
# - Evidence table: answers are constrained to retrieved snippets, with inline sources
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
# Data folder & schema
#   ./data/*.jsonl  with each line like:
#   {
#     "text": "Sowing time for cotton in Punjab is mid-April to mid-May. Recommended varieties: ...",
#     "source": "PAU_POP_Kharif_2024.pdf#p23",
#     "state": "Punjab",
#     "district": null,
#     "crop": "cotton",
#     "season": "Kharif",
#     "months": ["Apr","May"]        # 3-letter English month abbreviations
#   }
#   Tip: Chunk PDFs by section headings (Sowing time, Varieties, Seed rate, etc.)
#        and tag state, crop, season, months for that section.
# -----------------------------------------------------------------------------

import os
import re
import json
import time
import numpy as np
import faiss
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
from google import genai  # google-genai SDK
from glob import glob  # add near other imports

DATA_DIR = "./data"
# load ALL jsonl shards, including your new data_v5__state.jsonl files
DATA_GLOBS = ["*.jsonl"]   # you can narrow later: ["data.jsonl","data_v4__*.jsonl","data_v5__*.jsonl"]

# ---------- Config ----------
EMB_MODEL = "all-MiniLM-L6-v2"
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
GEMINI_MODEL = "gemini-2.5-flash-lite"
DATA_FILES = ["data", "data_v2", "data_v3", "data_v4__part0", "data_v4__part1"]
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
    "may":"May",
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
    "andaman and nicobar islands","puducherry","delhi","chandigarh","lakshadweep","daman and diu","dadra and nagar haveli"
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

def find_state(q: str) -> str:
    ql = q.lower()
    for s in INDIA_STATES:
        if s in ql:
            return s
    return None

def find_month(q: str) -> str:
    ql = q.lower()
    m = re.search(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|"
                  r"january|february|march|april|june|july|august|september|october|november|december)\b", ql)
    if m:
        return MONTHS_MAP[m.group(0)]
    return None

def detect_intent(q: str) -> str:
    ql = q.lower()
    if any(w in ql for w in ["when should i plant", "when to plant", "sowing time", "sow window", "plant in"]):
        return "sowing_window"
    if any(w in ql for w in ["variety", "seed variety", "hybrid", "cv"]):
        return "variety"
    if any(w in ql for w in ["price", "mandi", "sell", "market"]):
        return "market"
    if any(w in ql for w in ["fertilizer", "dose", "seed rate", "irrigat"]):
        return "pop_practice"
    return "general"

def parse_query(q: str) -> Dict[str, Any]:
    q_exp = expand_with_synonyms(q)
    return {
        "intent": detect_intent(q_exp),
        "state": find_state(q_exp),
        "month": find_month(q_exp),
        "raw": q_exp
    }

# ---------- Load docs ----------
docs = []
files = []
for pat in DATA_GLOBS:
    files.extend(sorted(glob(os.path.join(DATA_DIR, pat))))

if not files:
    raise RuntimeError(f"No JSONL files found in {DATA_DIR} (patterns: {DATA_GLOBS})")

total_lines = 0
for path in files:
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    docs.append(json.loads(line))
                    total_lines += 1
                except json.JSONDecodeError:
                    # skip bad lines but keep going
                    continue
    except FileNotFoundError:
        # ignore; glob might pick stale entries
        pass

if not docs:
    raise RuntimeError("No documents loaded. Put your .jsonl chunks in ./data/")

print(f"Loaded {len(docs)} documents from {len(files)} files.")

# ---------- Build corpus arrays (REQUIRED before indexing) ----------
texts = [d.get("text", "") for d in docs]

meta = [{
    "source": d.get("source", "unknown"),
    "state": (d.get("state") or "").lower() or None,
    "district": (d.get("district") or "").lower() or None,
    "crop": (d.get("crop") or "").lower() or None,
    "season": (d.get("season") or "").lower() or None,
    # ensure months is a list like ["May"]
    "months": (d.get("months") if isinstance(d.get("months"), list)
               else ([d.get("months")] if d.get("months") else None)),
} for d in docs]

# ---------- Build indices ----------
print(f"Loaded {len(docs)} documents.")
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
def filter_pool(signals: Dict[str, Any]) -> List[int]:
    pool = list(range(len(docs)))
    # hard filter by state
    if signals["state"]:
        s = signals["state"]
        pool = [i for i in pool if meta[i]["state"] == s]
    # hard filter by month
    if signals["month"]:
        mo = signals["month"]
        pool = [i for i in pool if meta[i]["months"] and mo in meta[i]["months"]]
    return pool

def rrf_fuse(bm_ranked: List[int], dense_ranked: List[int], k: int = RRF_K) -> List[int]:
    scores = {}
    for r, i in enumerate(bm_ranked):
        scores[i] = scores.get(i, 0.0) + 1.0 / (k + r + 1)
    for r, i in enumerate(dense_ranked):
        scores[i] = scores.get(i, 0.0) + 1.0 / (k + r + 1)
    fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [i for i,_ in fused]

def hybrid_search(q: str, k_fusion: int = TOP_K_FUSION, k_rerank: int = RERANK_KEEP) -> Tuple[Dict[str,Any], List[int]]:
    signals = parse_query(q)
    pool = filter_pool(signals)
    if not pool:
        pool = list(range(len(docs)))

    # BM25 over full then select pool by top scores
    bm_scores = bm25.get_scores(q.split())
    bm_pairs = [(i, bm_scores[i]) for i in pool]
    bm_ranked = [i for i,_ in sorted(bm_pairs, key=lambda x: x[1], reverse=True)[:k_fusion]]

    # Dense over full then filter to pool
    qv = embedder.encode([q], normalize_embeddings=True, convert_to_numpy=True)
    D, I = index.search(qv.astype("float32"), min(k_fusion*2, len(docs)))
    dense_filtered = [i for i in I[0] if i in pool][:k_fusion]

    # RRF fusion
    fused = rrf_fuse(bm_ranked, dense_filtered)
    fused = fused[:max(k_fusion, k_rerank)]

    # Cross-encoder rerank
    pairs = [[q, texts[i]] for i in fused]
    if not pairs:
        return signals, []
    rr_scores = reranker.predict(pairs)
    reranked = [i for i,_ in sorted(zip(fused, rr_scores), key=lambda x: x[1], reverse=True)]
    return signals, reranked[:k_rerank]

# ---------- Prompting ----------
def make_evidence(idxs: List[int], limit: int = MAX_CTX_SNIPPETS) -> List[Dict[str, str]]:
    ev = []
    seen = set()
    for i in idxs[:limit]:
        snip = texts[i].strip().replace("\n"," ")
        src = meta[i]["source"] or "unknown"
        key = (snip[:100], src)
        if key in seen: 
            continue
        seen.add(key)
        ev.append({"snippet": snip[:800], "source": src})
    return ev

def build_prompt(evidence: List[Dict[str,str]], user_query: str) -> str:
    ctx = "\n---\n".join([f"{e['snippet']}\n(Source: {e['source']})" for e in evidence])
    return f"""You are an agriculture assistant for Indian farmers.

POLICY
- Answer ONLY using EVIDENCE below: cite sources inline (title/section/page if present).
- If critical info is missing, ask ONE short clarifying question first, then stop.
- Be concise and actionable: show sowing window, varieties, seed rate, key cautions, and a simple next step.
- If you cannot ground a claim, do NOT state it.

EVIDENCE
{ctx}

USER QUESTION
{user_query}

Now produce:
1) A brief recommendation tailored to location/time in the question
2) Bullet points with specifics (dates, varieties, seed rates, etc.)
3) A 'Sources' list with the sources used
"""

def grounded_answer(q: str) -> str:
    signals, idxs = hybrid_search(q)
    # Clarify if sowing intent but no location/time
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

    prompt = build_prompt(evidence, q)
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
