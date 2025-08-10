# index_builder.py
# Build FAISS index once; then agent.py can load it in milliseconds.
# Usage:
#   python index_builder.py

import os, json, faiss, numpy as np, torch
from glob import glob
from sentence_transformers import SentenceTransformer

# ---------- Config ----------
DATA_DIR      = "./data"
DATA_GLOBS    = ["*.jsonl"]             # all shards
ART_DIR       = "./artifacts"
CORPUS_PATH   = os.path.join(ART_DIR, "corpus.jsonl")       # merged docs
INDEX_PATH    = os.path.join(ART_DIR, "index_flatip.faiss") # FAISS vector index

EMB_MODEL     = "all-MiniLM-L6-v2"
MAX_SEQ_LEN   = 256          # shorter = faster; safe for short lines
EMB_BATCH     = 256          # try 256–512 on M4 Pro; lower if you OOM
DOCS_PER_CALL = 4096         # how many texts to encode per encode() call

os.makedirs(ART_DIR, exist_ok=True)

# Prefer Apple GPU (Metal) if present
DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"[builder] Device: {DEVICE}")

def iter_docs():
    files = []
    for pat in DATA_GLOBS:
        files += sorted(glob(os.path.join(DATA_DIR, pat)))
    if not files:
        raise RuntimeError(f"No JSONL files in {DATA_DIR} (patterns: {DATA_GLOBS})")

    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                text = d.get("text", "")
                if not text:
                    continue
                yield d, text

def chunked(it, n):
    buf = []
    for x in it:
        buf.append(x)
        if len(buf) >= n:
            yield buf
            buf = []
    if buf:
        yield buf

def main():
    embedder = SentenceTransformer(EMB_MODEL, device=DEVICE)
    embedder.max_seq_length = MAX_SEQ_LEN
    dim = embedder.get_sentence_embedding_dimension()
    index = faiss.IndexFlatIP(dim)

    # Merge all docs into one corpus file while we build the index
    # (So agent.py can load docs from a single fast file.)
    # We append; if file exists and you want a clean rebuild, delete it first.
    if os.path.exists(CORPUS_PATH):
        os.remove(CORPUS_PATH)

    total = 0
    with open(CORPUS_PATH, "a", encoding="utf-8") as out_corpus:
        # Stream in moderately large groups to keep encode() efficient
        for group in chunked(iter_docs(), DOCS_PER_CALL):
            texts = [t for (_, t) in group]
            # encode on MPS/CPU with normalization for inner product search
            embs = embedder.encode(
                texts,
                batch_size=EMB_BATCH,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,  # outer loop prints progress
                device=DEVICE,
            )
            index.add(embs.astype("float32"))

            # write the original JSON lines (unaltered) to merged corpus
            for (d, _) in group:
                out_corpus.write(json.dumps(d, ensure_ascii=False) + "\n")

            total += len(group)
            if total % 20000 == 0:
                print(f"[builder] Indexed {total} docs…")

    faiss.write_index(index, INDEX_PATH)
    print(f"[builder] DONE. Docs: {total}")
    print(f"[builder] Wrote: {INDEX_PATH}")
    print(f"[builder] Wrote: {CORPUS_PATH}")

if __name__ == "__main__":
    # Optional: make CPU side chill a bit on Apple
    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    os.environ.setdefault("OMP_NUM_THREADS", "4")
    main()
