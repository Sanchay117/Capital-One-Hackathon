import json

INPUT_FILE = "../data.jsonl"
OUTPUT_FILE = "../data.jsonl"
CHUNK_SIZE = 4  # Number of sentences/chunks to merge at a time (adjust as needed)
MIN_LEN = 40
MAX_LEN = 1000

def merge_chunks(input_file, output_file, chunk_size=4):
    with open(input_file, encoding="utf-8") as f:
        lines = [json.loads(line) for line in f]
    
    merged = []
    buffer = []
    prev_source = None

    for entry in lines:
        text, source = entry["text"], entry["source"]

        if prev_source is not None and source != prev_source:
            # flush buffer
            for i in range(0, len(buffer), chunk_size):
                chunk = " ".join(buffer[i:i+chunk_size])
                if MIN_LEN < len(chunk) < MAX_LEN:
                    merged.append({"text": chunk, "source": prev_source})
            buffer = []

        buffer.append(text)
        prev_source = source

    # Flush remaining buffer
    if buffer:
        for i in range(0, len(buffer), chunk_size):
            chunk = " ".join(buffer[i:i+chunk_size])
            if MIN_LEN < len(chunk) < MAX_LEN:
                merged.append({"text": chunk, "source": prev_source})

    with open(output_file, "w", encoding="utf-8") as out_f:
        for m in merged:
            out_f.write(json.dumps(m, ensure_ascii=False) + "\n")

    print(f"✅ Merged and wrote {len(merged)} chunks to {output_file}")

if __name__ == "__main__":
    merge_chunks(INPUT_FILE, OUTPUT_FILE, CHUNK_SIZE)
