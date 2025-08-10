#!/usr/bin/env python3
import csv, json, os, re
from typing import Optional, Dict

# ---- Canonical mappings -----------------------------------------------------
CROP_CANON = {
    "arhar/tur": "pigeonpea",
    "tur": "pigeonpea",
    "arhar": "pigeonpea",
    "cotton(lint)": "cotton",
    "dry chillies": "chilli",
    "castor seed": "castor",
    "coconut": "coconut",
    "gram": "chickpea",      # common Indian usage
    "arecanut": "arecanut",
    "jute": "jute",
}

SEASON_MAP = {
    "kharif": "kharif",
    "rabi": "rabi",
    "whole year": "whole year",
    "annual": "whole year",
}

MONTHS_BY_SEASON = {
    # optional helper if you ever want to add months later
    "kharif": ["Jun","Jul","Aug","Sep","Oct"],
    "rabi":   ["Nov","Dec","Jan","Feb","Mar"],
    "whole year": None,
}

def _canon_crop(name: str) -> str:
    s = (name or "").strip().lower()
    return CROP_CANON.get(s, s)

def _canon_season(season: str) -> str:
    s = re.sub(r"\s+", " ", (season or "").strip().lower())
    return SEASON_MAP.get(s, s or None)

def _numfmt(x: str) -> Optional[str]:
    if x is None: return None
    s = str(x).strip()
    if s == "": return None
    try:
        v = float(s)
        return f"{int(v)}" if abs(v - round(v)) < 1e-9 else f"{v:.3f}"
    except Exception:
        return s  # keep raw if non-numeric

def _safe_name(s: str) -> str:
    s = s.strip() or "UNKNOWN"
    return re.sub(r"[^\w\-]+", "_", s)[:80]

# ---- Conversion -------------------------------------------------------------
def convert(csv_path: str, out_prefix: str, group_by_state: bool = False):
    base = os.path.basename(csv_path)
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            crop_raw   = (row.get("Crop") or "").strip()
            year_raw   = (row.get("Crop_Year") or "").strip()
            season_raw = (row.get("Season") or "").strip()
            state_raw  = (row.get("State") or "").strip()

            area = _numfmt(row.get("Area"))
            prod = _numfmt(row.get("Production"))
            rain = _numfmt(row.get("Annual_Rainfall"))
            fert = _numfmt(row.get("Fertilizer"))
            pest = _numfmt(row.get("Pesticide"))
            yld  = _numfmt(row.get("Yield"))

            # normalize
            crop   = _canon_crop(crop_raw)
            state  = (state_raw.lower() or None)
            season = _canon_season(season_raw)

            try:
                year = int(float(year_raw)) if year_raw else None
            except Exception:
                year = None

            # Compose short factual text (units kept as "source units" where unknown)
            bits = []
            if state: bits.append(f"State: {state_raw.strip()}.")
            if year is not None: bits.append(f"Year: {year}.")
            if season: bits.append(f"Season: {season}.")
            if crop: bits.append(f"Crop: {crop}.")
            if area is not None: bits.append(f"Area: {area} (source units).")
            if prod is not None: bits.append(f"Production: {prod} (source units).")
            if yld  is not None: bits.append(f"Yield: {yld} (source units/area).")
            if rain is not None: bits.append(f"Annual rainfall: {rain} mm.")
            if fert is not None: bits.append(f"Fertilizer: {fert} (source units).")
            if pest is not None: bits.append(f"Pesticide: {pest} (source units).")

            text = " ".join(bits) or f"Crop statistics record ({state_raw}, {year_raw})."

            rec: Dict = {
                "text": text,
                "source": f"{base}#state={state_raw}/year={year_raw}/crop={crop_raw}",
                "state": state,
                "crop": crop or None,
                "season": season,
                "metric": "crop_stats",
                "year": year,
                "months": None,  # season-only dataset; keep month filter from interfering
            }
            rows.append(rec)

    # Write file(s)
    os.makedirs(os.path.dirname(out_prefix), exist_ok=True)
    if group_by_state:
        buckets = {}
        for r in rows:
            key = r.get("state") or "unknown"
            buckets.setdefault(key, []).append(r)
        for st, items in buckets.items():
            out_path = f"{out_prefix}__{_safe_name(st)}.jsonl"
            with open(out_path, "w", encoding="utf-8") as out:
                for rec in items:
                    out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"✅ {len(items):5d} → {out_path}")
    else:
        out_path = f"{out_prefix}__crop_stats.jsonl"
        with open(out_path, "w", encoding="utf-8") as out:
            for rec in rows:
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"✅ {len(rows):5d} → {out_path}")

if __name__ == "__main__":
    # INPUT
    CSV_PATH = "../datasets/crop_yield.csv"
    # OUTPUT prefix (file(s) will be ../data/data_stats__*.jsonl)
    OUT_PREFIX = "../data/data_v7"
    # Toggle per-state sharding if you want smaller files:
    convert(CSV_PATH, OUT_PREFIX, group_by_state=True)
    print("🎉 Done.")
