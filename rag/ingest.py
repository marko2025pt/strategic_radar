# ingest.py
# Chunks, embeds, and upserts all KB documents into Pinecone.
# Run once to initialise the knowledge base. Re-running is safe — idempotent.

import os
import json
import re
import unicodedata
from pathlib import Path
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings

# ─────────────────────────────────────────────
# STEP 1 — Load environment variables
# ─────────────────────────────────────────────

# Load .env from project root regardless of where script is run from
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=True)

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX   = os.getenv("PINECONE_INDEX")
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")

# Debug — confirm keys are loading (remove after testing)
print(f"PINECONE_INDEX: {PINECONE_INDEX}")
print(f"OPENAI_API_KEY loaded: {'yes' if OPENAI_API_KEY and 'your' not in OPENAI_API_KEY else 'NO — check .env'}")
print(f"PINECONE_API_KEY loaded: {'yes' if PINECONE_API_KEY and 'your' not in PINECONE_API_KEY else 'NO — check .env'}")

KB_DIR = os.path.join(os.path.dirname(__file__), "kb")

# ─────────────────────────────────────────────
# STEP 2 — Initialise Pinecone
# ─────────────────────────────────────────────

pc = Pinecone(api_key=PINECONE_API_KEY)

if PINECONE_INDEX not in [idx.name for idx in pc.list_indexes()]:
    print(f"Creating Pinecone index: {PINECONE_INDEX}")
    pc.create_index(
        name=PINECONE_INDEX,
        dimension=1536,  # text-embedding-3-small dimension
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
else:
    print(f"Index already exists: {PINECONE_INDEX}")

index = pc.Index(PINECONE_INDEX)

# ─────────────────────────────────────────────
# STEP 3 — Helper + Chunking functions
# ─────────────────────────────────────────────

def make_ascii_id(text: str) -> str:
    """Converts a string to a safe ASCII ID for Pinecone."""
    # Normalise unicode characters (e.g. é → e, — → -)
    text = unicodedata.normalize("NFKD", text)
    # Encode to ASCII, ignore non-ASCII characters
    text = text.encode("ascii", "ignore").decode("ascii")
    # Lowercase, replace spaces and slashes with underscores
    text = text.strip().lower().replace(" ", "_").replace("/", "_")
    return text


def chunk_markdown_by_h2(filepath: str, chunk_type: str, document: str) -> list[dict]:
    """
    Splits a markdown file into chunks at every ## heading.
    Skips the document title (# heading) and any empty sections.
    Returns a list of dicts with text and metadata.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Split on ## headings (not ### or #)
    pattern = r'(?=^## .+$)'
    sections = re.split(pattern, content, flags=re.MULTILINE)
    sections = [s.strip() for s in sections if s.strip()]

    chunks = []
    for section in sections:
        lines = section.strip().splitlines()
        heading = lines[0].replace("## ", "").strip()

        # Skip chunks that are just the document title (# heading)
        if heading.startswith("#"):
            continue

        text = section.strip()

        chunks.append({
            "id": f"{document}::{make_ascii_id(heading)}",
            "text": text,
            "metadata": {
                "source": os.path.basename(filepath),
                "chunk_type": chunk_type,
                "heading": heading,
                "document": document
            }
        })

    return chunks


def chunk_competitor_registry(filepath: str) -> list[dict]:
    """
    Parses competitor_registry.json and reconstructs each competitor
    as a clean text block for embedding. Strips all JSON structure.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    chunks = []
    for competitor in data["competitors"]:
        also_known_as = ", ".join(competitor["also_known_as"]) if competitor["also_known_as"] else "N/A"
        key_verticals = ", ".join(competitor["key_verticals"])
        geographic_presence = ", ".join(competitor["geographic_presence"])

        text = f"""Competitor: {competitor["name"]}
Also known as: {also_known_as}
Headquarters: {competitor["headquarters"]}
Website: {competitor["website"]}
Primary Focus: {competitor["primary_focus"]}
Key Verticals: {key_verticals}
Geographic Presence: {geographic_presence}
Ownership: {competitor["ownership"]}
Why We Monitor: {competitor["why_we_monitor"]}"""

        chunks.append({
            "id": f"competitor_registry::{make_ascii_id(competitor['id'])}",
            "text": text,
            "metadata": {
                "source": "competitor_registry.json",
                "chunk_type": "competitor",
                "heading": competitor["name"],
                "document": "competitor_registry"
            }
        })

    return chunks

# ─────────────────────────────────────────────
# STEP 4 — Load and chunk all KB documents
# ─────────────────────────────────────────────

print("\nLoading and chunking KB documents...")

all_chunks = []

all_chunks += chunk_markdown_by_h2(
    filepath=os.path.join(KB_DIR, "business_profile.md"),
    chunk_type="business_profile",
    document="business_profile"
)

all_chunks += chunk_markdown_by_h2(
    filepath=os.path.join(KB_DIR, "strategic_direction.md"),
    chunk_type="strategic_objective",
    document="strategic_direction"
)

all_chunks += chunk_competitor_registry(
    filepath=os.path.join(KB_DIR, "competitor_registry.json")
)

all_chunks += chunk_markdown_by_h2(
    filepath=os.path.join(KB_DIR, "technology_watchlist.md"),
    chunk_type="technology",
    document="technology_watchlist"
)

print(f"Total chunks prepared: {len(all_chunks)}")

# Sanity check — print all chunk IDs
for chunk in all_chunks:
    print(f"  → {chunk['id']}")

# ─────────────────────────────────────────────
# STEP 5 — Embed each chunk
# ─────────────────────────────────────────────

print("\nEmbedding chunks...")

embeddings_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=OPENAI_API_KEY
)

texts = [chunk["text"] for chunk in all_chunks]
vectors = embeddings_model.embed_documents(texts)

print(f"Embeddings generated: {len(vectors)}")

# ─────────────────────────────────────────────
# STEP 6 — Upsert into Pinecone
# ─────────────────────────────────────────────

print("\nUpserting into Pinecone...")

upsert_data = []
for chunk, vector in zip(all_chunks, vectors):
    upsert_data.append({
        "id": chunk["id"],
        "values": vector,
        "metadata": {
            **chunk["metadata"],
            "text": chunk["text"]  # store text in metadata for retrieval
        }
    })

# Upsert in batches of 100
batch_size = 100
for i in range(0, len(upsert_data), batch_size):
    batch = upsert_data[i:i + batch_size]
    index.upsert(vectors=batch)
    print(f"  Upserted batch {i // batch_size + 1}: {len(batch)} vectors")

# ─────────────────────────────────────────────
# STEP 7 — Verify
# ─────────────────────────────────────────────

print("\nVerifying index...")

stats = index.describe_index_stats()
print(f"Total vectors in index: {stats['total_vector_count']}")
print("Expected: 24")

if stats['total_vector_count'] == 24:
    print("✅ Ingestion complete. Knowledge base is ready.")
else:
    print("⚠️  Vector count does not match expected. Check chunk output above.")