from huggingface_hub import InferenceClient
from sentence_transformers import SentenceTransformer
import faiss
import json
import numpy as np

# === Load Embedding Model ===
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# === Load Docs and Create FAISS Index ===
with open("data.jsonl") as f:
    docs = [json.loads(line) for line in f]

texts = [doc["text"] for doc in docs]
embeddings = embedder.encode(texts)
embedding_dim = embeddings[0].shape[0]

index = faiss.IndexFlatL2(embedding_dim)
index.add(np.array(embeddings))

# === Hugging Face LLM Client ===
client = InferenceClient(
    model="mistralai/Mistral-7B-Instruct-v0.1",  # or use flan-t5-xl, zephyr-7b-beta, etc.
    token="hf_XXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # Replace with your Hugging Face token
)

# === RAG Query Function ===
def generate_answer(user_query, k=3):
    # Embed the query
    query_embed = embedder.encode([user_query])
    D, I = index.search(np.array(query_embed), k=k)

    # Build context from top-k retrieved documents
    context = "\n".join(docs[i]["text"] for i in I[0])

    # Construct RAG prompt
    prompt = f"""You are an agriculture assistant for Indian farmers.
Answer clearly and only using the facts from the context.

Context:
{context}

Question:
{user_query}

Answer:"""

    # Call Hugging Face inference endpoint
    output = client.text_generation(
        prompt=prompt,
        max_new_tokens=200,
        temperature=0.2,
        stop_sequences=["\n"]
    )

    return output.strip()

# === CLI Interface ===
if __name__ == "__main__":
    print("🌾 Ask your agri-related question (Ctrl+C to quit):")
    while True:
        try:
            q = input("\n🟢 You: ")
            a = generate_answer(q)
            print(f"\n🧠 Agent:\n{a}")
        except KeyboardInterrupt:
            print("\n👋 Exiting.")
            break
