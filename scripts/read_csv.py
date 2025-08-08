import csv
import json
import os
import re
from collections import defaultdict

# --- Configure fields to include (label, CSV column key) ---
FIELDS = [
    ("Crop", "CROPS"),
    ("Type Of Crop", "TYPE_OF_CROP"),
    ("Soil", "SOIL"),
    ("Season", "SEASON"),
    ("Sown in", "SOWN"),
    ("Harvested in", "HARVESTED"),
    ("Water Source", "WATER_SOURCE"),
    ("Soil pH", "SOIL_PH"),
    ("Soil pH high", "SOIL_PH_HIGH"),
    ("Crop Duration", "CROPDURATION"),
    ("Crop Duration Max", "CROPDURATION_MAX"),
    ("Temperature", "TEMP"),
    ("Max Temperature", "MAX_TEMP"),
    ("Required Water", "WATERREQUIRED"),
    ("Required Water (MAX)", "WATERREQUIRED_MAX"),
    ("Relative Humidity", "RELATIVE_HUMIDITY"),
    ("Relative Humidity (MAX)", "RELATIVE_HUMIDITY_MAX"),
]

# --- Units to append for numeric values (tweak if your CSV uses different units) ---
UNITS = {
    "TEMP": "°C",
    "MAX_TEMP": "°C",
    "WATERREQUIRED": "mm",
    "WATERREQUIRED_MAX": "mm",
    "RELATIVE_HUMIDITY": "%",
    "RELATIVE_HUMIDITY_MAX": "%",
    "CROPDURATION": "days",
    "CROPDURATION_MAX": "days",
    # pH is unitless; SOWN/HARVESTED are months/strings so no unit.
}

def row_val(row, key):
    v = row.get(key, "")
    return "" if v is None else str(v).strip()

def _is_number(s: str) -> bool:
    try:
        float(s)
        return True
    except Exception:
        return False

def format_value(key, raw):
    """Append units when the value is numeric and a unit is defined."""
    if raw == "":
        return ""
    unit = UNITS.get(key)
    # if value already has a % and unit is %, don't double-append
    if unit == "%" and raw.endswith("%"):
        return raw
    # numeric check
    if _is_number(raw):
        # keep as-is or lightly format; here we avoid over-rounding
        val = float(raw)
        # show int if whole number, else one decimal
        s = f"{int(val)}" if abs(val - round(val)) < 1e-9 else f"{val:.1f}"
        return f"{s}{(' ' + unit) if unit else ''}"
    else:
        # non-numeric string (e.g., "Jun", "kharif")
        return raw

def row_to_text(row):
    parts = []
    for label, key in FIELDS:
        raw = row_val(row, key)
        if raw != "":
            parts.append(f"{label}: {format_value(key, raw)}")
    return ". ".join(parts) + "."

def _safe_name(s: str) -> str:
    """Filesystem-safe-ish filename chunk."""
    s = s.strip() or "UNKNOWN"
    s = re.sub(r"[^\w\-]+", "_", s, flags=re.UNICODE)  # spaces/punct -> _
    return s[:80]  # avoid overly long filenames

def csv_to_jsonl_sharded(csv_path, out_prefix, group_by=None, max_rows_per_file=50000):
    """
    If `group_by` is provided and exists in CSV, write one JSONL per group:
        {out_prefix}__{groupval}.jsonl
    Else, shard by count:
        {out_prefix}__part{N}.jsonl  (each ~max_rows_per_file rows)
    """
    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    base_csv = os.path.basename(csv_path)

    # --- Path 1: group-wise sharding ---
    if group_by and group_by in fieldnames:
        groups = defaultdict(list)
        for i, row in enumerate(rows):
            groups[row.get(group_by, "UNKNOWN")].append((i, row))

        for gval, items in groups.items():
            safe = _safe_name(str(gval))
            out_path = f"{out_prefix}__{safe}.jsonl"
            with open(out_path, "w", encoding="utf-8") as out:
                for idx, row in items:
                    text = row_to_text(row)
                    entry = {
                        "text": text,
                        "source": f"{base_csv}#{group_by}={gval}/row{idx}"
                    }
                    out.write(json.dumps(entry, ensure_ascii=False) + "\n")
            print(f"✅ Wrote {len(items)} rows → {out_path}")

    # --- Path 2: fixed-size shards ---
    else:
        part = -1
        out = None
        written_in_part = 0
        for idx, row in enumerate(rows):
            cur_part = idx // max_rows_per_file
            if cur_part != part:
                if out:
                    out.close()
                    print(f"✅ Wrote {written_in_part} rows → {out_path}")
                part = cur_part
                written_in_part = 0
                out_path = f"{out_prefix}__part{part}.jsonl"
                out = open(out_path, "w", encoding="utf-8")

            text = row_to_text(row)
            entry = {
                "text": text,
                "source": f"{base_csv}#row{idx}"
            }
            out.write(json.dumps(entry, ensure_ascii=False) + "\n")
            written_in_part += 1

        if out:
            out.close()
            print(f"✅ Wrote {written_in_part} rows → {out_path}")

if __name__ == "__main__":
    # INPUT CSV
    CSV_PATH = "../datasets/Crop_recommendation_dataset.csv"

    # OUTPUT prefix (files will be data_v4__*.jsonl)
    OUT_PREFIX = "../data/data_v4"

    # Try grouping by a column if it exists (e.g., "STATE"); else will shard by count.
    csv_to_jsonl_sharded(
        csv_path=CSV_PATH,
        out_prefix=OUT_PREFIX,
        group_by="STATE",          # change/remove if not present in your CSV
        max_rows_per_file=50000    # used only when group_by is absent
    )
    print("🎉 Done.")
