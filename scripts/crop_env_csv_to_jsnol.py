#!/usr/bin/env python3
"""
Convert two crop-environment CSVs into RAG-friendly JSONL.

CSV A (basic):
temperature,humidity,ph,rainfall,label,Label_Num

CSV B (with nutrients):
N,P,K,temperature,humidity,ph,rainfall,label

Output:
  ../data/data_env__basic.jsonl
  ../data/data_env__npk.jsonl

Each JSON line:
{
  "text": "Crop: rice. Conditions: temperature 21.8 °C; humidity 80.3 %; soil pH 7.04; rainfall 226.66 mm.",
  "source": "crop_env_basic.csv#row12",
  "state": null,
  "district": null,
  "crop": "rice",
  "season": null,
  "metric": "crop_env",
  "year": null,
  "months": null,
  "N": null, "P": null, "K": null,           # present in NPK file only
  "temperature": 21.77, "humidity": 80.32, "ph": 7.04, "rainfall": 226.66
}
"""

import csv, json, os, re
from typing import Optional, Dict, List

# ---------- CONFIG ----------
CSV_BASIC_PATH = "../datasets/Crop_production_data/Crop_Data.csv"     # <-- set to your first csv
CSV_NPK_PATH   = "../datasets/Crop_production_data/Crop_recommendation.csv"       # <-- set to your second csv
OUT_PREFIX     = "../data/data_v8"                   # files: data_env__basic.jsonl, data_env__npk.jsonl

# ---------- HELPERS ----------
MONTHS = {"Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"}  # not used here but kept for future

def _num(x, nd=2) -> Optional[float]:
    """Parse numeric → float with rounding; return None if blank."""
    if x is None: return None
    s = str(x).strip()
    if s == "": return None
    try:
        v = float(s)
        return float(f"{v:.{nd}f}")
    except Exception:
        return None

def _fmt(val: Optional[float], unit: str | None = None) -> str:
    if val is None: return "N/A"
    s = f"{int(val)}" if abs(val - round(val)) < 1e-9 else f"{val}"
    return f"{s}{(' ' + unit) if unit else ''}"

def _canon_crop(c: str) -> str:
    s = (c or "").strip().lower()
    # light canonicalization; extend as needed
    return {"arhar/tur":"pigeonpea", "cotton(lint)":"cotton"}.get(s, s)

def _write_jsonl(path: str, rows: List[Dict]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as out:
        for r in rows:
            out.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"✅ {len(rows)} → {path}")

# ---------- BUILDERS ----------
def build_basic_record(base: str, row_idx: int, r: Dict[str,str]) -> Dict:
    crop = _canon_crop(r.get("label"))
    t  = _num(r.get("temperature"))
    h  = _num(r.get("humidity"))
    pH = _num(r.get("ph"), nd=2)
    rf = _num(r.get("rainfall"))

    text = (
        f"Crop: {crop}. "
        f"Conditions: temperature {_fmt(t, '°C')}; humidity {_fmt(h, '%')}; "
        f"soil pH {_fmt(pH)}; rainfall {_fmt(rf, 'mm')}."
    )

    return {
        "text": text,
        "source": f"{base}#row{row_idx}",
        "state": None,
        "district": None,
        "crop": crop or None,
        "season": None,
        "metric": "crop_env",
        "year": None,
        "months": None,
        # numeric fields for potential downstream use
        "temperature": t, "humidity": h, "ph": pH, "rainfall": rf,
        "N": None, "P": None, "K": None,
        # carry-through label num if present
        "label_num": _num(r.get("Label_Num"), nd=0) if "Label_Num" in r else None,
    }

def build_npk_record(base: str, row_idx: int, r: Dict[str,str]) -> Dict:
    crop = _canon_crop(r.get("label"))
    N  = _num(r.get("N"), nd=0)
    P  = _num(r.get("P"), nd=0)
    K  = _num(r.get("K"), nd=0)
    t  = _num(r.get("temperature"))
    h  = _num(r.get("humidity"))
    pH = _num(r.get("ph"), nd=2)
    rf = _num(r.get("rainfall"))

    text = (
        f"Crop: {crop}. Conditions: temperature {_fmt(t, '°C')}; humidity {_fmt(h, '%')}; "
        f"soil pH {_fmt(pH)}; rainfall {_fmt(rf, 'mm')}. "
        f"Soil nutrients: N {_fmt(N)} (source units), P {_fmt(P)} (source units), K {_fmt(K)} (source units)."
    )

    return {
        "text": text,
        "source": f"{base}#row{row_idx}",
        "state": None,
        "district": None,
        "crop": crop or None,
        "season": None,
        "metric": "crop_env",
        "year": None,
        "months": None,
        "temperature": t, "humidity": h, "ph": pH, "rainfall": rf,
        "N": N, "P": P, "K": K,
    }

# ---------- MAIN ----------
def convert_basic(csv_path: str) -> List[Dict]:
    out = []
    base = os.path.basename(csv_path)
    with open(csv_path, newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for i, row in enumerate(rdr):
            out.append(build_basic_record(base, i, row))
    return out

def convert_npk(csv_path: str) -> List[Dict]:
    out = []
    base = os.path.basename(csv_path)
    with open(csv_path, newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for i, row in enumerate(rdr):
            out.append(build_npk_record(base, i, row))
    return out

if __name__ == "__main__":
    basic_rows = convert_basic(CSV_BASIC_PATH)
    npk_rows   = convert_npk(CSV_NPK_PATH)

    _write_jsonl(f"{OUT_PREFIX}__basic.jsonl", basic_rows)
    _write_jsonl(f"{OUT_PREFIX}__npk.jsonl", npk_rows)
    print("🎉 Done.")
