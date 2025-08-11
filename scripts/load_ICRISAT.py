# ingest_district_panel_csv.py
# Converts a wide "district-year crop panel" CSV into per-crop JSONL docs,
# chunked into N shards for fast indexing. No CLI; configure variables below.

import os, csv, json, math, re
from typing import Optional

# ----------------- CONFIG (edit these) -----------------
INPUT_CSV = "../datasets/ICRISAT-District-Level-Data.csv"
OUT_DIR   = "../data/"   # will be created
NUM_CHUNKS = 20
SOURCE_TAG = "ICRISAT-District-Level-Data.csv"            # used in the 'source' field
# -------------------------------------------------------

SEASON_MONTHS = {
    "kharif": ["Jun","Jul","Aug","Sep","Oct"],
    "rabi":   ["Nov","Dec","Jan","Feb","Mar"],
}

def norm(s: Optional[str]) -> str:
    return (s or "").strip()

def year_int(s: str) -> Optional[int]:
    m = re.search(r"(19|20)\d{2}", s or "")
    return int(m.group(0)) if m else None

def fnum(x: str) -> Optional[float]:
    if x is None: return None
    x = x.strip()
    if x == "" or x.lower() == "na": return None
    try:
        v = float(x)
        if v < 0:  # treat negatives (e.g., -1.0) as missing sentinel
            return None
        return v
    except:
        return None

def to_ha(area_th_ha: Optional[float]) -> Optional[float]:
    return None if area_th_ha is None else area_th_ha * 1000.0

def to_tonnes(prod_th_ton: Optional[float]) -> Optional[float]:
    return None if prod_th_ton is None else prod_th_ton * 1000.0

def build_text(state, district, year, crop, season, area_ha, prod_t, yld_kg_ha):
    parts = [f"State: {state}."]
    if district: parts.append(f"District: {district}.")
    if year is not None: parts.append(f"Year: {year}.")
    if season: parts.append(f"Season: {season.capitalize()}.")
    parts += [f"Crop: {crop}."]
    if area_ha is not None: parts.append(f"Area: {int(area_ha) if area_ha.is_integer() else round(area_ha,2)} ha.")
    if prod_t is not None: parts.append(f"Production: {int(prod_t) if prod_t and float(prod_t).is_integer() else (round(prod_t,2) if prod_t is not None else prod_t)} tonnes.")
    if yld_kg_ha is not None: parts.append(f"Yield: {yld_kg_ha} kg/ha.")
    return " ".join(parts)

# Map of column triples -> (canonical_crop, season)
# Keys are the EXACT column headers in your CSV
COLMAP = [
    (("RICE AREA (1000 ha)","RICE PRODUCTION (1000 tons)","RICE YIELD (Kg per ha)"), ("rice", None)),
    (("WHEAT AREA (1000 ha)","WHEAT PRODUCTION (1000 tons)","WHEAT YIELD (Kg per ha)"), ("wheat", None)),
    (("KHARIF SORGHUM AREA (1000 ha)","KHARIF SORGHUM PRODUCTION (1000 tons)","KHARIF SORGHUM YIELD (Kg per ha)"), ("sorghum","kharif")),
    (("RABI SORGHUM AREA (1000 ha)","RABI SORGHUM PRODUCTION (1000 tons)","RABI SORGHUM YIELD (Kg per ha)"), ("sorghum","rabi")),
    (("SORGHUM AREA (1000 ha)","SORGHUM PRODUCTION (1000 tons)","SORGHUM YIELD (Kg per ha)"), ("sorghum", None)),
    (("PEARL MILLET AREA (1000 ha)","PEARL MILLET PRODUCTION (1000 tons)","PEARL MILLET YIELD (Kg per ha)"), ("pearl millet", None)),
    (("MAIZE AREA (1000 ha)","MAIZE PRODUCTION (1000 tons)","MAIZE YIELD (Kg per ha)"), ("maize", None)),
    (("FINGER MILLET AREA (1000 ha)","FINGER MILLET PRODUCTION (1000 tons)","FINGER MILLET YIELD (Kg per ha)"), ("finger millet", None)),
    (("BARLEY AREA (1000 ha)","BARLEY PRODUCTION (1000 tons)","BARLEY YIELD (Kg per ha)"), ("barley", None)),
    (("CHICKPEA AREA (1000 ha)","CHICKPEA PRODUCTION (1000 tons)","CHICKPEA YIELD (Kg per ha)"), ("chickpea", None)),
    (("PIGEONPEA AREA (1000 ha)","PIGEONPEA PRODUCTION (1000 tons)","PIGEONPEA YIELD (Kg per ha)"), ("pigeonpea", None)),
    (("MINOR PULSES AREA (1000 ha)","MINOR PULSES PRODUCTION (1000 tons)","MINOR PULSES YIELD (Kg per ha)"), ("minor pulses", None)),
    (("GROUNDNUT AREA (1000 ha)","GROUNDNUT PRODUCTION (1000 tons)","GROUNDNUT YIELD (Kg per ha)"), ("groundnut", None)),
    (("SESAMUM AREA (1000 ha)","SESAMUM PRODUCTION (1000 tons)","SESAMUM YIELD (Kg per ha)"), ("sesamum", None)),
    (("RAPESEED AND MUSTARD AREA (1000 ha)","RAPESEED AND MUSTARD PRODUCTION (1000 tons)","RAPESEED AND MUSTARD YIELD (Kg per ha)"), ("rapeseed and mustard", None)),
    (("SAFFLOWER AREA (1000 ha)","SAFFLOWER PRODUCTION (1000 tons)","SAFFLOWER YIELD (Kg per ha)"), ("safflower", None)),
    (("CASTOR AREA (1000 ha)","CASTOR PRODUCTION (1000 tons)","CASTOR YIELD (Kg per ha)"), ("castor", None)),
    (("LINSEED AREA (1000 ha)","LINSEED PRODUCTION (1000 tons)","LINSEED YIELD (Kg per ha)"), ("linseed", None)),
    (("SUNFLOWER AREA (1000 ha)","SUNFLOWER PRODUCTION (1000 tons)","SUNFLOWER YIELD (Kg per ha)"), ("sunflower", None)),
    (("SOYABEAN AREA (1000 ha)","SOYABEAN PRODUCTION (1000 tons)","SOYABEAN YIELD (Kg per ha)"), ("soyabean", None)),
    (("OILSEEDS AREA (1000 ha)","OILSEEDS PRODUCTION (1000 tons)","OILSEEDS YIELD (Kg per ha)"), ("oilseeds", None)),
    (("SUGARCANE AREA (1000 ha)","SUGARCANE PRODUCTION (1000 tons)","SUGARCANE YIELD (Kg per ha)"), ("sugarcane", None)),
    (("COTTON AREA (1000 ha)","COTTON PRODUCTION (1000 tons)","COTTON YIELD (Kg per ha)"), ("cotton", None)),
    # Area-only classes:
    (("FRUITS AREA (1000 ha)",None,None), ("fruits", None)),
    (("VEGETABLES AREA (1000 ha)",None,None), ("vegetables", None)),
    (("FRUITS AND VEGETABLES AREA (1000 ha)",None,None), ("fruits and vegetables", None)),
    (("POTATOES AREA (1000 ha)",None,None), ("potatoes", None)),
    (("ONION AREA (1000 ha)",None,None), ("onion", None)),
    (("FODDER AREA (1000 ha)",None,None), ("fodder", None)),
]

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    writers = []
    files = []
    try:
        # open NUM_CHUNKS writers
        for k in range(NUM_CHUNKS):
            path = os.path.join(OUT_DIR, f"data_v12__{k:02d}.jsonl")
            f = open(path, "w", encoding="utf-8")
            files.append(f)
            writers.append(f)
        rr = 0  # round-robin pointer
        total_docs = 0

        with open(INPUT_CSV, "r", encoding="utf-8") as f:
            rdr = csv.DictReader(f)
            for ridx, row in enumerate(rdr, start=1):
                state = norm(row.get("State Name") or row.get("State"))
                dist  = norm(row.get("Dist Name") or row.get("District"))
                year_s = norm(row.get("Year"))
                year = year_int(year_s)

                # Lowercase meta
                state_l = state.lower() if state else None
                dist_l  = dist.lower() if dist else None

                for cols, (crop, season) in COLMAP:
                    area_col, prod_col, yld_col = cols
                    area = fnum(row.get(area_col)) if area_col else None
                    prod = fnum(row.get(prod_col)) if prod_col else None
                    yld  = fnum(row.get(yld_col)) if yld_col else None

                    # Skip empty/zero rows (keep zeros? choose to skip if both area and prod missing/zero)
                    has_area = (area is not None and area > 0)
                    has_prod = (prod is not None and prod > 0)
                    has_yld  = (yld  is not None and yld  > 0)
                    if not (has_area or has_prod or has_yld):
                        continue

                    area_ha = to_ha(area) if area is not None else None
                    prod_t  = to_tonnes(prod) if prod is not None else None
                    months = SEASON_MONTHS.get(season)

                    text = build_text(state, dist, year, crop, season, area_ha, prod_t, yld)

                    doc = {
                        "text": text,
                        "source": f"{SOURCE_TAG}#state={state}/district={dist}/crop={crop}/year={year_s}/season={season or 'annual'}",
                        "state": state_l,
                        "district": dist_l,
                        "crop": crop,                # keep lowercase canonical
                        "year": year,
                        "season": season,            # 'kharif'|'rabi'|None
                        "months": months,            # list or None
                        "metric": "crop_stats",
                        # optional raw/normalized numbers for downstream analysis/UI
                        "area": area_ha,
                        "area_units": "Hectare" if area_ha is not None else None,
                        "production": prod_t,
                        "production_units": "Tonnes" if prod_t is not None else None,
                        "yield": yld,               # kg/ha
                    }

                    writers[rr].write(json.dumps(doc, ensure_ascii=False) + "\n")
                    rr = (rr + 1) % NUM_CHUNKS
                    total_docs += 1

        print(f"Done. Wrote {total_docs} docs across {NUM_CHUNKS} chunks in: {OUT_DIR}")

    finally:
        for f in files:
            try: f.close()
            except: pass

if __name__ == "__main__":
    main()
