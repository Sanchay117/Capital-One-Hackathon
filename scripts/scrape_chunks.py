#!/usr/bin/env python3
"""
scrape_chunks.py

Usage examples
--------------
# fast crawl (no JS rendering)
python scrape_chunks.py https://example.com 200

# crawl with JS rendering (headless Chromium)
python scrape_chunks.py https://example.com 100 --render

The script:
• Breadth-first crawls pages on the same domain
• Optionally renders JavaScript using requests-html (pyppeteer)
• Extracts overlapping sentence-window chunks
• Appends them to data_v2.jsonl as:  {"text": ..., "source": ...}
"""

import sys, re, json, time, pathlib
from collections import deque
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

# ─── Optional JS rendering (requests-html) ──────────────────────────────────
from requests_html import HTMLSession             # pip install requests-html
session = HTMLSession()                           # reused across pages
# ────────────────────────────────────────────────────────────────────────────

# ─── Config ────────────────────────────────────────────────────────────────
OUTPUT_FILE          = pathlib.Path("../data_v2.jsonl")
MIN_LEN, MAX_LEN     = 40, 1000                  # chunk length bounds
CRAWL_DELAY_SECONDS  = 3.0
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0.0.0 Safari/537.36"),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/"
}
# ────────────────────────────────────────────────────────────────────────────

# flag toggled from CLI
RENDER_JS = True

# ─── Helper functions ──────────────────────────────────────────────────────
def get_domain(url: str) -> str:
    return urlparse(url).netloc

def normalize_url(base: str, href: str) -> str | None:
    """Convert a raw href into an absolute HTTP/HTTPS URL for the same domain."""
    if not href or href.startswith(("#", "mailto:", "javascript:", "tel:")):
        return None
    try:
        abs_url = urljoin(base, href.split("#")[0])
        parsed  = urlparse(abs_url)
        if parsed.scheme not in ("http", "https"):
            return None
        return abs_url
    except ValueError:
        # malformed URI, invalid IPv6 literal, etc.
        return None

def fetch_html(url: str) -> str:
    """
    Return HTML for `url`.
    • If RENDER_JS is False → simple requests.get()
    • If RENDER_JS is True  → render with requests_html (headless Chromium)
    """
    if not RENDER_JS:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        return r.text

    # JS-rendered branch
    r = session.get(url, timeout=20)
    # render() executes JS; adjust timeouts as needed
    r.html.render(timeout=25, sleep=1, wait=0.5)
    return r.html.html

def extract_chunks(text: str, window: int = 3, stride: int = 2) -> list[str]:
    """Sliding window of `window` sentences with `stride` overlap."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks, i = [], 0
    while i < len(sentences):
        chunk = " ".join(sentences[i : i + window])
        if MIN_LEN < len(chunk) < MAX_LEN:
            chunks.append(chunk)
        i += stride
    return chunks

def extract_html_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)

# ─── BFS crawler ───────────────────────────────────────────────────────────
def crawl_site(start_url: str, max_pages: int = 100):
    domain   = get_domain(start_url)
    visited  = set()
    queue    = deque([start_url])

    while queue and len(visited) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        try:
            html = fetch_html(url)
        except Exception as e:
            print(f"⚠️  Failed to fetch {url}: {e}", file=sys.stderr)
            continue

        print(f"✅ Crawled: {url}", file=sys.stderr)
        yield url, html                                  # HTML page

        # enqueue same-domain links
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            link = normalize_url(url, a["href"])
            if link and get_domain(link) == domain and link not in visited:
                queue.append(link)

        time.sleep(CRAWL_DELAY_SECONDS)

# ─── Main workflow ─────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    # optional --render flag
    global RENDER_JS
    if "--render" in sys.argv:
        RENDER_JS = True
        sys.argv.remove("--render")

    start_url = sys.argv[1]
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 100

    with OUTPUT_FILE.open("a", encoding="utf-8") as out_f:
        for url, html in crawl_site(start_url, max_pages):
            text = extract_html_text(html)
            for chunk in extract_chunks(text):
                rec = {"text": chunk, "source": url}
                out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"\n✨ Finished. Appended records to {OUTPUT_FILE.absolute()}")

# ────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
