#!/usr/bin/env python3
"""
scrape.py

Usage:
    python scrape.py https://example.com [max_pages]

Crawls the given site (same domain only), extracts text, splits into sentences,
and writes JSONL records to tasks.jsonl with fields {"text", "source"}.
"""

import sys
import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from collections import deque
import pathlib

def get_domain(url):
    return urlparse(url).netloc

def normalize_url(base, link):
    return urljoin(base, link.split('#')[0])

def extract_sentences(text):
    # simple sentence splitter; tweak regex if needed
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if 40 < len(s) < 300]

def crawl_site(start_url, max_pages=100):
    domain = get_domain(start_url)
    visited = set()
    queue = deque([start_url])
    pages = []

    while queue and len(visited) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"⚠️  Failed to fetch {url}: {e}", file=sys.stderr)
            continue

        print(f"✅ Crawled: {url}", file=sys.stderr)
        pages.append((url, resp.text))

        # find same-site links
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", href=True):
            link = normalize_url(url, a['href'])
            if get_domain(link) == domain and link not in visited:
                queue.append(link)

    return pages

def extract_text(html):
    soup = BeautifulSoup(html, "html.parser")
    # remove scripts/styles
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(separator=' ', strip=True)

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    start_url = sys.argv[1]
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 100

    out_path = pathlib.Path("../data.jsonl")
    with out_path.open("a", encoding="utf-8") as out_f:
        for url, html in crawl_site(start_url, max_pages):
            text = extract_text(html)
            # print(url,html,text)
            for sentence in extract_sentences(text):
                record = {"text": sentence, "source": url}
                out_f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\n✨ Finished. Appended records to {out_path}.")

if __name__ == "__main__":
    main()
