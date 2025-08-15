import os
import json
import numpy as np
import faiss
from dotenv import load_dotenv
from pathlib import Path
from sentence_transformers import SentenceTransformer
from google import genai                    

# === ENV & keys ==============================================================
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("Set GEMINI_API_KEY or GOOGLE_API_KEY in your .env or shell!")

# === Gemini client ===========================================================
GEMINI_MODEL = "models/gemini-1.5-flash" 
client = genai.Client(api_key=GEMINI_API_KEY) 

# === Embeddings & vector DB ==================================================
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
    resp = client.models.generate_content( 
        model=GEMINI_MODEL,
        contents=prompt,
    )
    return resp.text.strip()

def get_gemini_response(user_query, language="en"):
    """
    Generates a response from the Gemini model using RAG, tailored to a specific language.
    """
    # 1. Perform RAG search to find relevant context (same as generate_answer)
    q_embed = embedder.encode([user_query])
    _, idxs = index.search(np.array(q_embed), 3) # k=3

    # 2. Build the context from retrieved documents
    context = build_context_with_sources(idxs[0])

    # 3. Create a new prompt that instructs the model to use the specified language
    final_query = (
        f"Based on the context provided, answer the following question: '{user_query}'. "
        f"Please provide the entire response in the language with code: {language}."
    )
    prompt = build_prompt(context, final_query)

    # 4. Call the Gemini API
    resp = client.models.generate_content( 
        model=GEMINI_MODEL,
        contents=prompt,
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