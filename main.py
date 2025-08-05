from huggingface_hub import InferenceClient
from sentence_transformers import SentenceTransformer
import faiss
import json
import numpy as np
import os
from dotenv import load_dotenv

# === Load ENV Variables ===
load_dotenv()

HF_API_KEY = os.environ["HUGGING_FACE_API_KEY"]

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
    model="HuggingFaceH4/zephyr-7b-alpha",
    token=HF_API_KEY
)

# === Helper to Build Numbered, Sourced Context ===
def build_context_with_sources(idxs):
    """Context as fact (Source: name) per line, no numbers."""
    return "\n".join(
        f"{docs[i]['text']} (Source: {docs[i]['source']})" for i in idxs
    )

def build_prompt(context, user_query):
    return f"""You are an agriculture assistant for Indian farmers.

    Use ONLY the facts in the CONTEXT below to answer. When you use a fact, explicitly mention the source (e.g., 'as per IMD Bulletin').  
    If you cannot answer from the context, you may answer from your own knowledge, but BEGIN your answer with:  
    "⚠️ This answer is not grounded in the retrieved data. Please verify independently."

    CONTEXT:
    {context}

    QUESTION:
    {user_query}

    ANSWER:
    """

# === RAG Query Function ===
def generate_answer(user_query, k=3):
    # Embed and search
    query_embed = embedder.encode([user_query])
    D, I = index.search(np.array(query_embed), k=k)

    # Build context string with sources
    context = build_context_with_sources(I[0])

    # Build prompt
    prompt = build_prompt(context, user_query)

    # Call Hugging Face inference endpoint
    output = client.text_generation(
        prompt=prompt,
        max_new_tokens=200,
        temperature=0.2,
        stop=["\n"]
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

