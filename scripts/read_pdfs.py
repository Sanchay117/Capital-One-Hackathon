import os
import json
from PyPDF2 import PdfReader
import nltk

# Ensure the punkt tokenizer is available
nltk.download('punkt')

def extract_pdf_text(pdf_path):
    """
    Extract text from a PDF file using PyPDF2.
    """
    reader = PdfReader(pdf_path)
    text_chunks = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        text_chunks.append(page_text)
    return "\n".join(text_chunks)

def chunk_sentences(text, window_size=10, stride=5):
    """
    Split text into a sliding window of sentences.
    - window_size: number of sentences per chunk
    - stride: step size between windows
    """
    sentences = nltk.tokenize.sent_tokenize(text)
    chunks = []
    for start in range(0, max(1, len(sentences) - window_size + 1), stride):
        chunk = " ".join(sentences[start:start + window_size])
        chunks.append(chunk)
    # make sure to include tail if smaller than window_size
    if len(sentences) < window_size:
        chunks = [" ".join(sentences)]
    return chunks

def build_corpus(base_dir, output_path, window_size=10, stride=5):
    """
    Walk through all PDFs, extract sliding-window chunks of sentences,
    and write each chunk as a JSON line with its source.
    """
    with open(output_path, 'a', encoding='utf-8') as out_file:
        for root, _, files in os.walk(base_dir):
            for fname in files:
                if not fname.lower().endswith('.pdf'):
                    continue
                pdf_path = os.path.join(root, fname)
                rel_path = os.path.relpath(pdf_path, base_dir)
                text = extract_pdf_text(pdf_path)
                for idx, chunk in enumerate(chunk_sentences(text, window_size, stride)):
                    entry = {
                        "text": chunk,
                        "source": f"{rel_path}#chunk{idx}"
                    }
                    out_file.write(json.dumps(entry, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    BASE_DIR = "../datasets/agrollm_dataset"
    OUTPUT_FILE = "../data_v3.jsonl"
    WINDOW_SIZE = 10   # sentences per chunk
    STRIDE = 5         # overlap by half
    build_corpus(BASE_DIR, OUTPUT_FILE, WINDOW_SIZE, STRIDE)
    print(f"✅ Corpus with sliding-window chunks written to {OUTPUT_FILE}")
