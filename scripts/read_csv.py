#!/usr/bin/env python3
import csv, json, os, re
from typing import Optional, Dict, List

# Map messy headers → canonical month tokens and labels
MONTH_KEY = {
    "JUN": "Jun",
    "JUL": "Jul",
    "AUG": "Aug",
    "SEP": "Sep",
    "SEPT": "Sep",         # some sheets use SEPT
    "JUN-SEPT": "Monsoon", # aggregate
}

MONSOON_MONTHS = ["Jun", "Jul", "Aug", "Sep"]

def numfmt(x) -> Optional[str]:
    """Pretty formatting for numbers: int if whole, else one decimal."""
    if x is None or x == "":
        return None
    try:
        v = float(x)
    except Exception:
        return None
    return f"{int(v)}" if abs(v - round(v)) < 1e-9 else f"{v:.1f}"

def build_month_record(base_src: str, year: int, abbr: str, actual_mm: Optional[str], dep_pct: Optional[str]) -> Optional[Dict]:
    if actual_mm is None and dep_pct is None:
        return None
    text_bits = [f"Year: {year}. Month: {abbr}. Monsoon rainfall"]
    if actual_mm is not None:
        text_bits.append(f"{actual_mm} mm")
    if dep_pct is not None:
        # include explicit plus sign for positive departures to aid parsing
        sign_val = dep_pct if dep_pct.startswith("-") or dep_pct.startswith("+") else (f"+{dep_pct}" if not dep_pct.startswith("-") else dep_pct)
        text_bits.append(f"(departure {sign_val}%)")
    text = " ".join(text_bits) + ". This record is from IMD monsoon statistics (rainfall, departure)."
    return {
        "text": text,
        "source": f"{base_src}#year={year}/month={abbr}",
        "state": None,                # dataset is all-India unless you add a region
        "region": "all-india",
        "metric": "rainfall",
        "year": year,
        "months": [abbr],
    }

def build_agg_record(base_src: str, year: int, total_mm: Optional[str], dep_pct: Optional[str]) -> Optional[Dict]:
    if total_mm is None and dep_pct is None:
        return None
    text = (f"Year: {year}. Monsoon (Jun–Sep) total rainfall: "
            f"{total_mm + ' mm' if total_mm else 'N/A'}"
            f"{' (departure ' + (dep_pct if dep_pct.startswith('-') or dep_pct.startswith('+') else ('+'+dep_pct)) + '%)' if dep_pct else ''}."
            " This is an all-India IMD monsoon aggregate.")
    return {
        "text": text,
        "source": f"{base_src}#year={year}/season=Jun-Sep",
        "state": None,
        "region": "all-india",
        "metric": "rainfall",
        "year": year,
        "months": MONSOON_MONTHS[:],   # list of the four months
        "season": "Monsoon",
    }

def convert(csv_path: str, out_prefix: str):
    base_csv = os.path.basename(csv_path)
    out_path = f"{out_prefix}__monsoon.jsonl"
    records: List[Dict] = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # normalize headers (strip spaces)
        headers = [h.strip() for h in (reader.fieldnames or [])]

        for row in reader:
            # parse year
            y_raw = (row.get("YEAR") or row.get("Year") or "").strip()
            if not y_raw or not re.fullmatch(r"\d{4}", y_raw):
                # skip malformed year rows
                continue
            year = int(y_raw)

            # Gather monthly fields
            for raw_mon, abbr in MONTH_KEY.items():
                if raw_mon == "JUN-SEPT":
                    continue  # handle aggregate later
                # handle both "Actual Rainfall: JUN" and "Actual Rainfall: SEPT"
                actual_key = f"Actual Rainfall: {raw_mon}"
                dep_key = f"Departure Percentage: {raw_mon if raw_mon != 'SEPT' else 'SEP'}"
                a = numfmt(row.get(actual_key, "").strip())
                d = numfmt(row.get(dep_key, "").strip())
                rec = build_month_record(base_csv, year, abbr, a, d)
                if rec:
                    records.append(rec)

            # Aggregate Jun–Sep
            total_key = "Actual Rainfall: JUN-SEPT"
            dep_tot_key = "Departure Percentage: JUN-SEPT"
            a_tot = numfmt(row.get(total_key, "").strip())
            d_tot = numfmt(row.get(dep_tot_key, "").strip())
            agg = build_agg_record(base_csv, year, a_tot, d_tot)
            if agg:
                records.append(agg)

    # Write JSONL
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as out:
        for rec in records:
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"✅ Wrote {len(records)} records → {out_path}")

if __name__ == "__main__":
    # INPUT CSV (your sample schema)
    CSV_PATH = "../datasets/nw_India_rainfall_act_dep_1901_2015.csv"
    # Output prefix; file will be something like ../data/data_rain__monsoon.jsonl
    OUT_PREFIX = "../data/data_v6"
    convert(CSV_PATH, OUT_PREFIX)
    print("🎉 Done.")
