#!/usr/bin/env python3
import os, re, json
from collections import defaultdict
from typing import Optional, List, Dict

import pandas as pd  # requires pandas + openpyxl

# --- Header normalization ----------------------------------------------------
def norm_key(s: str) -> str:
    s = re.sub(r"[\s\-\.\[\]\(\)/]+", "_", str(s)).strip("_")
    s = re.sub(r"[^A-Za-z0-9_]+", "", s)
    return s.upper()

def normalize_headers(cols: List[str]) -> Dict[str, str]:
    """
    Map messy headers to canonical keys used downstream.
    Handles: 'Wholesale_Price [Rs. Per Quintal]', 'Temperature (Celsis)', 'Rainfall in mm', etc.
    """
    mapping = {}
    for c in cols:
        nk = norm_key(c)
        # direct matches
        if nk in ("YEAR","MONTH","STATE","CROP"):
            mapping[c] = nk
            continue
        # price variants
        if "PRICE" in nk or "WHOLESALE" in nk:
            mapping[c] = "PRICE"; continue
        # temperature (any spelling)
        if "TEMPERATURE" in nk:
            mapping[c] = "TEMP"; continue
        # rainfall variants
        if "RAINFALL" in nk or nk.endswith("_IN_MM"):
            mapping[c] = "RAINFALL"; continue
        mapping[c] = nk  # keep normalized for debug
    return mapping

# --- Month handling ----------------------------------------------------------
MONTHS_MAP = {
    "JANUARY":"Jan","JAN":"Jan","1":"Jan","01":"Jan",
    "FEBRUARY":"Feb","FEB":"Feb","2":"Feb","02":"Feb",
    "MARCH":"Mar","MAR":"Mar","3":"Mar","03":"Mar",
    "APRIL":"Apr","APR":"Apr","4":"Apr","04":"Apr",
    "MAY":"May","5":"May","05":"May",
    "JUNE":"Jun","JUN":"Jun","6":"Jun","06":"Jun",
    "JULY":"Jul","JUL":"Jul","7":"Jul","07":"Jul",
    "AUGUST":"Aug","AUG":"Aug","8":"Aug","08":"Aug",
    "SEPTEMBER":"Sep","SEP":"Sep","9":"Sep","09":"Sep",
    "OCTOBER":"Oct","OCT":"Oct","10":"Oct",
    "NOVEMBER":"Nov","NOV":"Nov","11":"Nov",
    "DECEMBER":"Dec","DEC":"Dec","12":"Dec",
}

def month_abbrev(val) -> Optional[str]:
    if val is None: return None
    s = str(val).strip()
    if not s: return None
    # 5.0 -> 5
    if re.fullmatch(r"\d+(\.0+)?", s):
        s = str(int(float(s)))
    return MONTHS_MAP.get(s.upper()) or MONTHS_MAP.get(s.capitalize())

# --- Formatting --------------------------------------------------------------
def is_number(x) -> bool:
    try:
        float(str(x)); return True
    except Exception:
        return False

def fmt_price(x) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)): return ""
    s = str(x).strip()
    if not s: return ""
    try:
        v = float(s)
        s = f"{int(v)}" if abs(v - round(v)) < 1e-9 else f"{v:.1f}"
    except Exception:
        pass
    return f"₹{s}/qtl"

def fmt_num(x, unit: str) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)): return ""
    try:
        v = float(x)
        s = f"{int(v)}" if abs(v - round(v)) < 1e-9 else f"{v:.1f}"
        return f"{s} {unit}"
    except Exception:
        return str(x)

def row_to_text(r: Dict) -> str:
    parts = []
    if r.get("STATE"): parts.append(f"State: {r['STATE']}")
    if r.get("YEAR") is not None: parts.append(f"Year: {r['YEAR']}")
    if r.get("MONTH_ABBR"): parts.append(f"Month: {r['MONTH_ABBR']}")
    if r.get("CROP"): parts.append(f"Crop: {r['CROP']}")
    if r.get("PRICE") not in (None, "", float("nan")):
        fp = fmt_price(r.get("PRICE"))
        if fp: parts.append(f"Wholesale Price: {fp}")
    if r.get("TEMP") not in (None, ""):
        ft = fmt_num(r.get("TEMP"), "°C")
        if ft: parts.append(f"Temperature: {ft}")
    if r.get("RAINFALL") not in (None, ""):
        fr = fmt_num(r.get("RAINFALL"), "mm")
        if fr: parts.append(f"Rainfall: {fr}")
    return ". ".join(parts) + "."

# --- Main conversion ---------------------------------------------------------
def produce_jsonl(input_path: str, out_prefix: str, sheet: Optional[str] = None, group_by: Optional[str] = "STATE"):
    df = pd.read_excel(input_path, sheet_name=sheet) if input_path.lower().endswith((".xlsx",".xls",".xlsm")) \
         else pd.read_csv(input_path)
    df = df.where(pd.notnull(df), None)

    # normalize headers, rename
    header_map = normalize_headers(list(df.columns))
    df = df.rename(columns=header_map)

    # coerce basics
    if "YEAR" in df.columns:
        df["YEAR"] = [int(x) if is_number(x) else x for x in df["YEAR"]]
    if "MONTH" in df.columns:
        df["MONTH_ABBR"] = [month_abbrev(x) for x in df["MONTH"]]
    else:
        df["MONTH_ABBR"] = None

    for col in ("STATE","CROP","PRICE","TEMP","RAINFALL"):
        if col not in df.columns: df[col] = None

    rows = df.to_dict(orient="records")
    base = os.path.basename(input_path)
    src_label = base + (f"[sheet={sheet}]" if sheet else "")

    if group_by and group_by in df.columns:
        buckets = defaultdict(list)
        for i, r in enumerate(rows):
            buckets[r.get(group_by) or "UNKNOWN"].append((i, r))
        for gval, items in buckets.items():
            safe = re.sub(r"[^\w\-]+","_", str(gval)).strip("_") or "UNKNOWN"
            out_path = f"{out_prefix}__{safe}.jsonl"
            with open(out_path, "w", encoding="utf-8") as out:
                for idx, r in items:
                    entry = {
                        "text": row_to_text(r),
                        "source": f"{src_label}#{group_by}={gval}/row{idx}",
                        "state": (str(r.get("STATE") or "").lower() or None),
                        "crop": r.get("CROP") or None,
                        "year": r.get("YEAR"),
                        "months": [r["MONTH_ABBR"]] if r.get("MONTH_ABBR") else None,
                    }
                    out.write(json.dumps(entry, ensure_ascii=False) + "\n")
            print(f"✅ Wrote {len(items)} rows → {out_path}")
    else:
        out_path = f"{out_prefix}__part0.jsonl"
        with open(out_path, "w", encoding="utf-8") as out:
            for idx, r in enumerate(rows):
                entry = {
                    "text": row_to_text(r),
                    "source": f"{src_label}#row{idx}",
                    "state": (str(r.get("STATE") or "").lower() or None),
                    "crop": r.get("CROP") or None,
                    "year": r.get("YEAR"),
                    "months": [r["MONTH_ABBR"]] if r.get("MONTH_ABBR") else None,
                }
                out.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"✅ Wrote {len(rows)} rows → {out_path}")

if __name__ == "__main__":
    INPUT = "../datasets/Wholesale_Crop_Prices_with_Weather_Data_India.xlsx"
    SHEET = "Sheet1"                                             # e.g., "Sheet1"
    OUT_PREFIX = "../data/data_v5"
    produce_jsonl(INPUT, OUT_PREFIX, sheet=SHEET, group_by="STATE")
    print("🎉 Done.")
