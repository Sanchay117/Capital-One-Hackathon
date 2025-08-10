#!/usr/bin/env python3
import csv, json, os, re
from typing import Dict, List, Optional

# ---- Paths (change to your filenames) ---------------------------------------
CSV_PATH   = "../datasets/government_schemes.csv"
OUT_PREFIX = "../data/data_v9"   # -> data_schemes__all.jsonl (and optionally per-state)

# ---- Known Indian states/UTs (lowercase) ------------------------------------
INDIA_STATES = {
    "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh",
    "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand", "karnataka",
    "kerala", "madhya pradesh", "maharashtra", "manipur", "meghalaya", "mizoram",
    "nagaland", "odisha", "punjab", "rajasthan", "sikkim", "tamil nadu", "telangana",
    "tripura", "uttar pradesh", "uttarakhand", "west bengal",
    "andaman and nicobar islands", "chandigarh", "dadra and nagar haveli", "daman and diu",
    "delhi", "jammu and kashmir", "ladakh", "lakshadweep", "puducherry"
}

MONTHS = {"Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"}  # not used here

def _clean_text(s: Optional[str]) -> str:
    if s is None: return ""
    # remove zero-width / BOM-ish chars and compress whitespace
    s = s.replace("\ufeff", "").replace("\u200b", "").replace("\u200c", "").replace("\u200d", "")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _first_sentence(s: str, max_len: int = 220) -> str:
    s = _clean_text(s)
    # take up to first period OR crop safely at ~max_len
    m = re.search(r"[.!?]\s", s)
    out = s[:m.start()+1] if m else s
    if len(out) > max_len:
        out = out[:max_len].rsplit(" ", 1)[0] + "…"
    return out

def _detect_state(*chunks: str) -> Optional[str]:
    blob = (" ".join(chunks or [])).lower()
    # look for exact state names first
    for st in sorted(INDIA_STATES, key=len, reverse=True):
        if re.search(rf"\b{re.escape(st)}\b", blob):
            return st
    return None

def _infer_level(level_raw: str) -> Optional[str]:
    s = _clean_text(level_raw).lower()
    if "central" in s: return "central"
    if "state" in s: return "state"
    return s or None

def _split_tags(s: str) -> List[str]:
    s = _clean_text(s)
    if not s: return []
    parts = [p.strip() for p in re.split(r"[;,]", s) if p.strip()]
    return parts

def _build_snippet(name: str, level: Optional[str], state: Optional[str],
                   benefits: str, eligibility: str) -> str:
    lvl = (level.title() if level else "Unknown level")
    juri = (state.title() if (level == "state" and state) else ("India" if level == "central" else None))
    lead = f"Scheme: {name.strip()}."
    scope = f" Level: {lvl}" + (f" ({juri})." if juri else ".")
    b = _first_sentence(benefits) if benefits else ""
    e = _first_sentence(eligibility) if eligibility else ""
    extra = " Benefit: " + b if b else ""
    if e:
        extra += " Eligibility: " + e
    return (lead + scope + extra).strip()

def convert(csv_path: str, out_prefix: str, per_state: bool = False):
    base = os.path.basename(csv_path)
    rows: List[Dict] = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        # some files may have a blank header column; DictReader keeps it as "" or None
        for i, r in enumerate(rdr):
            name        = _clean_text(r.get("scheme_name") or "")
            slug        = _clean_text(r.get("slug") or "")
            details     = _clean_text(r.get("details") or "")
            benefits    = _clean_text(r.get("benefits") or "")
            eligibility = _clean_text(r.get("eligibility") or "")
            application = _clean_text(r.get("application") or "")
            documents   = _clean_text(r.get("documents") or "")
            level       = _infer_level(r.get("level") or "")
            category    = _clean_text(r.get("schemeCategory") or "")
            tags        = _split_tags(r.get("tags") or "")

            # Try to detect state from any text fields if level says "state"
            state = _detect_state(name, details, eligibility, application, documents) if level == "state" else None

            text = _build_snippet(name, level, state, benefits, eligibility)

            rec = {
                "text": text,
                "source": f"{base}#slug={slug or _clean_text(name)}/row{i}",
                "metric": "scheme",
                "scheme_name": name or None,
                "slug": slug or None,
                "level": level,               # "state" | "central" | None
                "state": state,               # lowercase state if applicable
                "scheme_category": category or None,
                "tags": tags or None,
                # keep rich fields for grounded answers
                "details": details or None,
                "benefits": benefits or None,
                "eligibility": eligibility or None,
                "application": application or None,
                "documents": documents or None,
                # align with your agent schema
                "district": None,
                "crop": None,
                "season": None,
                "year": None,
                "months": None,
            }
            rows.append(rec)

    os.makedirs(os.path.dirname(out_prefix), exist_ok=True)
    if per_state:
        buckets: Dict[str, List[Dict]] = {}
        for r in rows:
            key = r.get("state") or "unknown"
            buckets.setdefault(key, []).append(r)
        for st, items in buckets.items():
            out_path = f"{out_prefix}__{re.sub(r'[^\\w-]+','_', st)[:80]}.jsonl"
            with open(out_path, "w", encoding="utf-8") as out:
                for rec in items:
                    out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"✅ {len(items):4d} → {out_path}")
    else:
        out_path = f"{out_prefix}__all.jsonl"
        with open(out_path, "w", encoding="utf-8") as out:
            for rec in rows:
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"✅ {len(rows):4d} → {out_path}")

if __name__ == "__main__":
    convert(CSV_PATH, OUT_PREFIX, per_state=False)
    print("🎉 Done.")
