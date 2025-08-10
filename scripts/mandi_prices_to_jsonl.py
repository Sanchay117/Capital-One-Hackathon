#!/usr/bin/env python3
import csv, json, os, re
from datetime import datetime
from typing import Optional, Dict, List

# ---------- Paths (edit as needed) ----------
CSV_PATH   = "../datasets/Agriculture_price_dataset.csv"
OUT_PATH   = "../data/data_v10.jsonl"

# Price unit label shown in the snippet
PRICE_UNIT = "₹/qtl"   # change to match your source if different

# ---------- Helpers ----------
MONTH_ABBR = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def _clean(s: Optional[str]) -> str:
    if s is None: return ""
    return re.sub(r"\s+", " ", s.replace("\ufeff","")).strip()

def _num(s: Optional[str]) -> Optional[float]:
    if s is None: return None
    t = _clean(s)
    if not t: return None
    try:
        return float(t)
    except Exception:
        return None

def _parse_date(s: str) -> Optional[datetime]:
    s = _clean(s)
    for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    return None

def _fmt_price(v: Optional[float]) -> str:
    if v is None: return "N/A"
    # keep integers if whole, else one decimal
    return f"{int(v)}" if abs(v - round(v)) < 1e-9 else f"{v:.1f}"

def _safe_month(dt: Optional[datetime]) -> Optional[str]:
    if not dt: return None
    return MONTH_ABBR[dt.month - 1]

# ---------- Build one record ----------
def build_record(base: str, idx: int, r: Dict[str,str]) -> Dict:
    state    = _clean(r.get("STATE")).lower() or None
    district = _clean(r.get("District Name")).lower() or None
    market   = _clean(r.get("Market Name")) or None
    commodity= _clean(r.get("Commodity")) or None
    variety  = _clean(r.get("Variety")) or None
    grade    = _clean(r.get("Grade")) or None
    min_p    = _num(r.get("Min_Price"))
    max_p    = _num(r.get("Max_Price"))
    modal_p  = _num(r.get("Modal_Price"))
    d_raw    = _clean(r.get("Price Date"))
    dt       = _parse_date(d_raw)
    year     = dt.year if dt else None
    month    = _safe_month(dt)

    # concise, BM25/semantic-friendly text
    when = dt.strftime("%Y-%m-%d") if dt else d_raw
    parts = [
        f"State: {state.title() if state else 'Unknown'}",
        f"District: {district.title() if district else 'Unknown'}",
        f"Market: {market}" if market else None,
        f"Commodity: {commodity}" + (f" (Variety: {variety})" if variety else ""),
        f"Grade: {grade}" if grade else None,
        f"Price on {when}: modal {_fmt_price(modal_p)} {PRICE_UNIT}"
        + (f" (min {_fmt_price(min_p)}, max {_fmt_price(max_p)})" if (min_p is not None or max_p is not None) else "")
    ]
    text = ". ".join(p for p in parts if p) + "."

    return {
        "text": text,
        "source": f"{base}#state={state or 'unknown'}/district={district or 'unknown'}/market={market or 'unknown'}/row{idx}",
        "metric": "market_price",
        "state": state,
        "district": district,
        "crop": commodity.lower() if commodity else None,   # align with your agent’s 'crop' meta
        "season": None,
        "year": year,
        "months": [month] if month else None,
        # keep raw fields for richer answers
        "market_name": market,
        "commodity": commodity,
        "variety": variety or None,
        "grade": grade or None,
        "min_price": min_p,
        "max_price": max_p,
        "modal_price": modal_p,
        "price_unit": PRICE_UNIT,
        "price_date": when,
    }

# ---------- Main ----------
def convert(csv_path: str, out_path: str):
    base = os.path.basename(csv_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    n = 0
    with open(csv_path, newline="", encoding="utf-8") as f, open(out_path, "w", encoding="utf-8") as out:
        rdr = csv.DictReader(f)
        for i, row in enumerate(rdr):
            rec = build_record(base, i, row)
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    print(f"✅ {n} → {out_path}")

if __name__ == "__main__":
    convert(CSV_PATH, OUT_PATH)
    print("🎉 Done.")
