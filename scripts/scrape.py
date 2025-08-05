#!/usr/bin/env python3
"""
scrape.py

Usage:
    python scrape.py https://example.com [max_pages]

Crawls the given site (same domain only), fetches HTML & PDF pages,
extracts text, splits into sentences, and writes JSONL records to data.jsonl
with fields {"text", "source"}.
"""

import sys, re, json, time
from collections import deque
from urllib.parse import urlparse, urljoin
import pathlib

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from io import BytesIO
from pdf2image import convert_from_bytes
import pytesseract

# ─── Config ──────────────────────────────────────────────────────────────────
OUTPUT_FILE = pathlib.Path("../test.jsonl")
MIN_LEN, MAX_LEN = 40, 300           # sentence length bounds
CRAWL_DELAY = 1.0                    # seconds between requests
# ─────────────────────────────────────────────────────────────────────────────

def get_domain(url):
    return urlparse(url).netloc

def normalize_url(base, link):
    return urljoin(base, link.split('#')[0])

def extract_sentences(text):
    # simple sentence splitter; adjust if needed
    parts = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in parts if MIN_LEN < len(s) < MAX_LEN]

def extract_pdf_text(pdf_bytes):
    # First try the fast pypdf route
    reader = PdfReader(BytesIO(pdf_bytes))
    pages_text = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        pages_text.append(txt.replace('\n', ' '))
    full_txt = " ".join(pages_text).strip()
    if len(full_txt) > 100:
        return full_txt

    # Fallback to OCR if embedded text is too short
    images = convert_from_bytes(pdf_bytes, dpi=200)
    ocr_text = []
    for img in images:
        ocr_text.append(pytesseract.image_to_string(img))
    return " ".join(ocr_text).replace('\n', ' ')

def extract_html_text(html):
    soup = BeautifulSoup(html, "html.parser")
    # remove scripts/styles
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)

def crawl_site(start_url, max_pages=100):
    domain = get_domain(start_url)
    visited = set()
    queue   = deque([start_url])
    pages   = []

    while queue and len(visited) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        try:
            resp = requests.get(url, timeout=10, headers={
                "User-Agent": "MyAgriBot/1.0 (+mailto:you@domain)"
            })
            resp.raise_for_status()
        except Exception as e:
            print(f"⚠️ Failed to fetch {url}: {e}", file=sys.stderr)
            continue

        print(f"✅ Crawled: {url}", file=sys.stderr)
        ctype = resp.headers.get("Content-Type", "").lower()

        if url.lower().endswith(".pdf") or "application/pdf" in ctype:
            # PDF page
            pages.append((url, resp.content, "pdf"))
        else:
            # HTML page
            html = resp.text
            pages.append((url, html, "html"))

            # enqueue same-site links
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                link = normalize_url(url, a["href"])
                if get_domain(link) == domain and link not in visited:
                    queue.append(link)

        time.sleep(CRAWL_DELAY)

    return pages

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    start_url = sys.argv[1]
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 100

    with OUTPUT_FILE.open("a", encoding="utf-8") as out_f:
        for url, content, kind in crawl_site(start_url, max_pages):
            if kind == "pdf":
                text = extract_pdf_text(content)
            else:
                text = extract_html_text(content)

            for sentence in extract_sentences(text):
                rec = {"text": sentence, "source": url}
                out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"\n✨ Finished. Appended records to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
