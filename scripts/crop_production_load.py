# ingest_crop_stats_csv_chunked.py
# Convert a crop-stats CSV to 10 JSONL shards compatible with your RAG pipeline.

import os, csv, json, re

# ======= CONFIG (edit these) =======
INPUT_CSV            = "../datasets/India_Agriculture_Crop_Production.csv"
OUT_DIR              = "../data"
BASENAME             = "data_v11"   # output prefix
NUM_CHUNKS           = 10                      # fixed to 10 per your ask
INFER_SEASON_MONTHS  = True                    # map Kharif/Rabi/Zaid to months
# ===================================

SEASON_TO_MONTHS = {
    "kharif": ["Jun", "Jul", "Aug", "Sep", "Oct"],
    "rabi":   ["Nov", "Dec", "Jan", "Feb", "Mar"],
    "zaid":   ["Apr", "May", "Jun"],
    "whole year": None,   # leave None so month filter doesn't over-constrain
}

def year_start_int(ystr: str) -> int | None:
    # "2001-02" -> 2001, "2003-2004" -> 2003, "2003" -> 2003
    m = re.search(r"(19|20)\d{2}", ystr or "")
    return int(m.group(0)) if m else None

def norm(s: str) -> str:
    return (s or "").strip()

def build_text(state, district, crop, year_str, season, area, area_units, prod, prod_units, yld):
    parts = [
        f"State: {state}.",
        f"District: {district}." if district else "",
        f"Year: {year_str}.",
        f"Season: {season}.",
        f"Crop: {crop}.",
        f"Area: {area} {area_units}.",
        f"Production: {prod} {prod_units}.",
        f"Yield: {yld}.",
    ]
    return " ".join(p for p in parts if p)

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    # open N chunk files
    paths = [os.path.join(OUT_DIR, f"{BASENAME}__part{idx+1:02}.jsonl") for idx in range(NUM_CHUNKS)]
    # truncate/create
    writers = [open(p, "w", encoding="utf-8") for p in paths]
    counts = [0] * NUM_CHUNKS

    total = 0
    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            state      = norm(row.get("State"))
            district   = norm(row.get("District"))
            crop       = norm(row.get("Crop"))
            year_str   = norm(row.get("Year"))
            season     = norm(row.get("Season"))
            area       = norm(row.get("Area"))
            area_units = norm(row.get("Area Units"))
            prod       = norm(row.get("Production"))
            prod_units = norm(row.get("Production Units"))
            yld        = norm(row.get("Yield"))

            text = build_text(state, district, crop, year_str, season, area, area_units, prod, prod_units, yld)

            y_start = year_start_int(year_str)
            months = None
            if INFER_SEASON_MONTHS and season:
                months = SEASON_TO_MONTHS.get(season.lower())

            doc = {
                "text": text,
                "source": f"{os.path.basename(INPUT_CSV)}#state={state}/district={district}/crop={crop}/year={year_str}/row{i}",
                "state": state.lower() or None,
                "district": district.lower() or None,
                "crop": crop.lower() or None,
                "year": y_start,
                "season": (season.lower() or None),
                "months": months,                 # None or ["Jun","Jul",...]
                "metric": "crop_stats",
                # raw fields (optional, handy later)
                "area": area, "area_units": area_units,
                "production": prod, "production_units": prod_units,
                "yield": yld,
            }

            # round-robin chunking to keep files roughly equal
            bucket = (i - 1) % NUM_CHUNKS
            writers[bucket].write(json.dumps(doc, ensure_ascii=False) + "\n")
            counts[bucket] += 1
            total += 1

    for w in writers:
        w.close()

    print(f"Wrote {total} docs into {NUM_CHUNKS} files:")
    for p, c in zip(paths, counts):
        print(f"  {os.path.basename(p)}  —  {c} rows")

if __name__ == "__main__":
    main()
