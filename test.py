# pip install google-genai python-dotenv

import os
from dotenv import load_dotenv
from google import genai

load_dotenv()                       # <-- reads .env into os.environ

key = os.getenv("GOOGLE_API_KEY")   # or use os.getenv("GEMINI_API_KEY") if you prefer
client = genai.Client(api_key=key)  # pass it explicitly

resp = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents="Explain how AI works in a few words",
)
print(resp.text)
