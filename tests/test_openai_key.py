# tests/test_openai_key.py
# Quick test to validate OpenAI API key and make a simple LLM call.

import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load .env from project root
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print(f"API Key loaded: {'yes' if OPENAI_API_KEY and 'your' not in OPENAI_API_KEY else 'NO — check .env'}")
print(f"Key preview: {OPENAI_API_KEY[:10]}...")

# ─────────────────────────────────────────────
# TEST 1 — Simple LLM call
# ─────────────────────────────────────────────

print("\n--- TEST 1: LLM Call ---")
try:
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say hello in one sentence."}],
        max_tokens=50
    )
    print(f"✅ LLM call successful")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ LLM call failed: {e}")

# ─────────────────────────────────────────────
# TEST 2 — Embeddings call
# ─────────────────────────────────────────────

print("\n--- TEST 2: Embeddings Call ---")
try:
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input="This is a test sentence for embeddings."
    )
    vector = response.data[0].embedding
    print(f"✅ Embeddings call successful")
    print(f"Vector dimension: {len(vector)}")
    print(f"First 5 values: {vector[:5]}")
except Exception as e:
    print(f"❌ Embeddings call failed: {e}")