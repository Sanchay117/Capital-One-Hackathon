from llama_cpp import Llama
from sentence_transformers import SentenceTransformer
import faiss, json, numpy as np

# === Load LLM ===
llm = Llama(
    model_path="./models/mistral-7b-instruct-v0.1.Q5_K_M.gguf",
    n_ctx=2048,
    n_threads=12,  # use your core count
    n_gpu_layers=33  # offload as much to GPU as fits
)

# === Load Embedding Model ===
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# === Load and Embed KB ===
with open("data.jsonl") as f:
    docs = [json.loads(line) for line in f]

texts = [doc["text"] for doc in docs]
embeddings = embedder.encode(texts)
index = faiss.IndexFlatL2(embeddings[0].shape[0])
index.add(np.array(embeddings))

# === RAG Query Function ===
def generate_answer(user_query):
    query_embed = embedder.encode([user_query])
    D, I = index.search(np.array(query_embed), k=2)
    context = "\n".join(docs[i]["text"] for i in I[0])

    prompt = f"""You are an agriculture assistant for Indian farmers.
        Answer clearly and only using the facts from the context.

        Context:
        {context}

        Question:
        {user_query}

        Answer:"""

    result = llm(prompt, max_tokens=200, temperature=0.2)
    return result["choices"][0]["text"]

# === Run it ===
if __name__ == "__main__":
    q = input("Ask me something about agriculture: ")
    print(generate_answer(q))
