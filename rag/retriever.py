# rag/retriever.py
# Pinecone query layer — retrieves relevant KB chunks for a given query.
# Called by LangGraph nodes during signal evaluation.

import os
from pathlib import Path
from dotenv import load_dotenv
from pinecone import Pinecone
from pinecone.exceptions import PineconeApiException
from langchain_openai import OpenAIEmbeddings
from openai import AuthenticationError, RateLimitError, APIConnectionError

from core.logging_config import get_logger

logger = get_logger(__name__)

# ─────────────────────────────────────────────
# Load environment variables
# ─────────────────────────────────────────────

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=True)

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX   = os.getenv("PINECONE_INDEX")
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")

# ─────────────────────────────────────────────
# Initialise clients
# ─────────────────────────────────────────────

try:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX)
    logger.info(f"Pinecone client initialised — index: {PINECONE_INDEX}")
except PineconeApiException as e:
    logger.critical(f"Failed to initialise Pinecone client: {e}", exc_info=True)
    raise
except Exception as e:
    logger.critical(f"Unexpected error initialising Pinecone: {e}", exc_info=True)
    raise

try:
    embeddings_model = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=OPENAI_API_KEY
    )
    logger.info("OpenAI embeddings model initialised")
except Exception as e:
    logger.critical(f"Failed to initialise OpenAI embeddings model: {e}", exc_info=True)
    raise

# ─────────────────────────────────────────────
# Core retrieval function
# ─────────────────────────────────────────────

def retrieve(query: str, top_k: int = 3, chunk_type: str = None) -> list[dict]:
    """
    Retrieves the most relevant KB chunks for a given query.

    Args:
        query:      Natural language query string
        top_k:      Number of chunks to return (default 3)
        chunk_type: Optional filter — 'business_profile', 'strategic_objective',
                    'competitor', or 'technology'

    Returns:
        List of dicts with 'text', 'chunk_type', 'heading', 'score'
        Returns empty list on failure — never raises.
    """

    logger.info(f"Retrieving chunks — query: '{query}' | top_k: {top_k} | chunk_type: {chunk_type or 'any'}")

    # ── Step 1: Embed the query ──
    try:
        query_vector = embeddings_model.embed_query(query)
        logger.debug(f"Query embedded successfully — vector dim: {len(query_vector)}")
    except AuthenticationError as e:
        logger.error(f"OpenAI authentication failed — check OPENAI_API_KEY: {e}", exc_info=True)
        return []
    except RateLimitError as e:
        logger.warning(f"OpenAI rate limit hit during embedding: {e}", exc_info=True)
        return []
    except APIConnectionError as e:
        logger.error(f"OpenAI connection error during embedding: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Unexpected error during embedding: {e}", exc_info=True)
        return []

    # ── Step 2: Build filter ──
    filter_dict = {"chunk_type": {"$eq": chunk_type}} if chunk_type else None

    # ── Step 3: Query Pinecone ──
    try:
        results = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict
        )
        logger.debug(f"Pinecone query returned {len(results['matches'])} matches")
    except PineconeApiException as e:
        logger.error(f"Pinecone query failed: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Unexpected error querying Pinecone: {e}", exc_info=True)
        return []

    # ── Step 4: Validate and format results ──
    if not results["matches"]:
        logger.warning(f"Pinecone returned 0 results for query: '{query}'")
        return []

    chunks = []
    for match in results["matches"]:
        try:
            chunks.append({
                "text":       match["metadata"].get("text", ""),
                "chunk_type": match["metadata"].get("chunk_type", ""),
                "heading":    match["metadata"].get("heading", ""),
                "document":   match["metadata"].get("document", ""),
                "score":      round(match["score"], 4)
            })
        except Exception as e:
            logger.warning(f"Skipping malformed match — could not parse metadata: {e}")
            continue

    logger.info(f"Retrieved {len(chunks)} chunks — top score: {chunks[0]['score'] if chunks else 'N/A'}")
    return chunks


# ─────────────────────────────────────────────
# Convenience wrappers
# ─────────────────────────────────────────────

def retrieve_strategic_objectives(query: str, top_k: int = 3) -> list[dict]:
    """Retrieves strategic objectives most relevant to a signal."""
    logger.debug(f"retrieve_strategic_objectives called — query: '{query}'")
    return retrieve(query, top_k=top_k, chunk_type="strategic_objective")


def retrieve_business_profile(query: str, top_k: int = 2) -> list[dict]:
    """Retrieves business profile chunks most relevant to a query."""
    logger.debug(f"retrieve_business_profile called — query: '{query}'")
    return retrieve(query, top_k=top_k, chunk_type="business_profile")


def retrieve_competitor(competitor_name: str) -> list[dict]:
    """Retrieves the profile for a specific competitor."""
    logger.debug(f"retrieve_competitor called — competitor: '{competitor_name}'")
    return retrieve(competitor_name, top_k=1, chunk_type="competitor")


def retrieve_technologies(query: str, top_k: int = 2) -> list[dict]:
    """Retrieves technology watchlist chunks most relevant to a query."""
    logger.debug(f"retrieve_technologies called — query: '{query}'")
    return retrieve(query, top_k=top_k, chunk_type="technology")