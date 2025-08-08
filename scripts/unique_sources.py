#!/usr/bin/env python3

"""
Usage:
python3 unique_sources.py ../data/data.jsonl --show-urls --max-urls 5
"""

import argparse, json, re, sys
from collections import Counter, defaultdict
from urllib.parse import urlsplit

def normalize_domain(url: str) -> str | None:
    if not url:
        return None
    s = url.strip()
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', s):
        s = 'http://' + s
    try:
        netloc = urlsplit(s).netloc
    except Exception:
        return None
    if not netloc:
        return None
    host = netloc.split('@')[-1].split(':')[0].lower().strip('.')
    if host.startswith('www.'):
        host = host[4:]
    return host or None

def iter_jsonl(path: str):
    with (sys.stdin if path == '-' else open(path, 'r', encoding='utf-8')) as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                print(f"⚠️  Skipping line {ln}: invalid JSON ({e})", file=sys.stderr)

def main():
    ap = argparse.ArgumentParser(
        description="Extract unique source domains (and counts) from a JSONL file with a 'source' field."
    )
    ap.add_argument("jsonl", help="Path to JSONL file (use '-' for stdin)")
    ap.add_argument("--show-urls", dest="show_urls", action="store_true",
                    help="Also list the distinct source URLs for each domain")
    ap.add_argument("--max-urls", type=int, default=10,
                    help="Max URLs to show per domain (with --show-urls)")
    args = ap.parse_args()

    counts = Counter()
    urls_by_domain = defaultdict(set)

    for obj in iter_jsonl(args.jsonl):
        src = obj.get("source")
        dom = normalize_domain(src)
        if dom:
            counts[dom] += 1
            urls_by_domain[dom].add(src)

    if not counts:
        print("No domains found.", file=sys.stderr)
        sys.exit(1)

    print(f"Unique domains: {len(counts)}")
    for dom, c in counts.most_common():
        print(f"{dom}\t{c}")
        if args.show_urls:
            for u in sorted(urls_by_domain[dom])[:args.max_urls]:
                print(f"  - {u}")

if __name__ == "__main__":
    main()
