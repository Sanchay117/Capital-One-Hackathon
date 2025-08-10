import os
import json
import numpy as np
import faiss
from dotenv import load_dotenv
from pathlib import Path
from sentence_transformers import SentenceTransformer
from google import genai                     # <-- google-genai SDK

# === ENV & keys ==============================================================
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("Set GEMINI_API_KEY in your .env or shell!")

# === Gemini client ===========================================================
GEMINI_MODEL = "gemini-2.5-flash-lite"
gemini = genai.Client(api_key=GEMINI_API_KEY)

# === Embeddings & vector DB ==================================================
# locate project root and data file
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
DATA_FILE = PROJECT_ROOT / "data" / "data.jsonl"
embedder = SentenceTransformer("all-MiniLM-L6-v2")

with open(DATA_FILE, encoding="utf-8") as f:
    docs = [json.loads(line) for line in f]

texts       = [d["text"] for d in docs]
embeddings  = embedder.encode(texts)
dim         = embeddings[0].shape[0]

index = faiss.IndexFlatL2(dim)
index.add(np.array(embeddings))

# === Prompt helpers ==========================================================
def build_context_with_sources(idxs):
    return "\n".join(f"{docs[i]['text']} (Source: {docs[i]['source']})" for i in idxs)

def build_prompt(context, user_query):
    return f"""You are an agriculture assistant for Indian farmers.

        POLICY  
        • If the answer is in CONTEXT → cite sources and answer feel free to draw logical conclusions related to the question from the context.  
        • **If the answer is NOT in CONTEXT → you MUST do BOTH of the following, in order:**  
        1. Print the exact line below (with emoji):  
            ⚠️ This answer is not grounded in the retrieved data. Please verify independently.  
        2. Immediately after that line, give your best answer from general knowledge.

        CONTEXT  
        {context}

        QUESTION  
        {user_query}

        ---
        Provide the answer here:
    """

# === RAG function ============================================================
def generate_answer(user_query, k=3):
    # 1 NN search
    q_embed = embedder.encode([user_query])
    _, idxs = index.search(np.array(q_embed), k)

    # 2 prompt construction
    context = build_context_with_sources(idxs[0])
    prompt  = build_prompt(context, user_query)

    # 3 Gemini call
    resp = gemini.models.generate_content(
        model     = GEMINI_MODEL,
        contents  = prompt,
    )
    return resp.text.strip()

# === CLI loop ================================================================
if __name__ == "__main__":
    print("🌾  Ask your agri-related question (Ctrl+C to quit):")
    try:
        while True:
            q = input("\n🟢 You: ")
            print("\n🧠 Agent:\n" + generate_answer(q))
    except KeyboardInterrupt:
        print("\n👋 Exiting.")