import os
import json
import re
from PyPDF2 import PdfReader

def extract_pdf_text(pdf_path):
    reader = PdfReader(pdf_path)
    pages = [p.extract_text() or "" for p in reader.pages]
    return "\n".join(pages)

def split_sentences(text):
    # split on end-of-sentence punctuation + whitespace
    # keeps the punctuation on the sentence
    return re.split(r'(?<=[\.\?\!])\s+', text.strip())

def chunk_sentences(text, window_size=10, stride=5):
    sentences = split_sentences(text)
    if len(sentences) <= window_size:
        return [" ".join(sentences)]
    chunks = []
    for start in range(0, len(sentences) - window_size + 1, stride):
        chunks.append(" ".join(sentences[start:start + window_size]))
    # include final tail chunk if it wasn't covered
    last_start = len(sentences) - window_size
    if (len(sentences) - window_size) % stride != 0:
        chunks.append(" ".join(sentences[last_start:]))
    return chunks

def build_corpus(base_dir, output_path, window_size=10, stride=5):
    with open(output_path, 'w', encoding='utf-8') as out_file:
        for root, _, files in os.walk(base_dir):
            for fname in files:
                if not fname.lower().endswith('.pdf'):
                    continue
                path = os.path.join(root, fname)
                rel = os.path.relpath(path, base_dir)
                text = extract_pdf_text(path)
                for i, chunk in enumerate(chunk_sentences(text, window_size, stride)):
                    entry = {
                        "text": chunk,
                        "source": f"{rel}#chunk{i}"
                    }
                    out_file.write(json.dumps(entry, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    BASE_DIR = "../datasets/agrollm_dataset/Agricultural_management"
    OUTPUT_FILE = "../test.jsonl"
    build_corpus(BASE_DIR, OUTPUT_FILE)
    print(f"✅ Written sliding-window corpus to {OUTPUT_FILE}")