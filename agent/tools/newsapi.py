# Version 1.1 — Final demo delivery to Ironhack 2026-03-06
"""
agent/tools/newsapi.py

NewsAPI tool for the Strategic Radar agent.

NewsAPI provides structured news articles from 80,000+ sources
with keyword search and date filtering. Used as the secondary
signal discovery tool alongside Tavily.

MCP integration: in-process using @mcp.tool() decorator.
Shared FastMCP instance and utilities imported from utils.py.

Free tier limitation: 30 days max lookback, capped at 28 days
in this implementation to avoid UTC boundary errors.
"""

import os
from datetime import datetime, timedelta
from newsapi import NewsApiClient
from newsapi.newsapi_exception import NewsAPIException
from core.logging_config import get_logger
from agent.tools.utils import mcp, _classify_source

logger = get_logger(__name__)


def _get_client() -> NewsApiClient:
    """
    Returns an authenticated NewsAPI client.
    Raises RuntimeError if API key is missing.
    """
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        raise RuntimeError("NEWS_API_KEY is not set in environment")
    return NewsApiClient(api_key=api_key)


def _days_to_date(days: int) -> str:
    """
    Converts a day count to an ISO date string for NewsAPI's from parameter.
    Example: 7 → "2026-02-24"
    """
    from_date = datetime.utcnow() - timedelta(days=days)
    return from_date.strftime("%Y-%m-%d")


@mcp.tool()
def newsapi_search(query: str, time_range_days: int = 7) -> list[dict]:
    """
    Searches NewsAPI for recent articles matching the query.

    Args:
        query:           Search string to execute.
        time_range_days: How many days back to search (7, 14, or 30).

    Returns:
        List of RawSignal dicts. Empty list on failure.
    """
    logger.info(f"newsapi_search — query='{query}' | days={time_range_days}")

    try:
        client = _get_client()

        # Cap at 28 days to stay within free tier limit safely
        safe_days = min(time_range_days, 28)
        from_date = _days_to_date(safe_days)

        response = client.get_everything(
            q=query,
            from_param=from_date,
            language="en",
            sort_by="relevancy",
            page_size=5,
        )

        articles = response.get("articles", [])
        signals = []

        for a in articles:
            source = a.get("source", {})
            url = a.get("url", "")

            title = a.get("title", "") or ""
            description = a.get("description", "") or ""
            snippet = description if description else title

            signal = {
                "title":        title,
                "url":          url,
                "snippet":      snippet,
                "source":       source.get("name", ""),
                "published_at": a.get("publishedAt", ""),
                "source_type":  _classify_source(url),
                "api_origin":   "newsapi",
            }
            signals.append(signal)

        logger.info(f"newsapi_search — OK — returned {len(signals)} signals")
        logger.debug(f"newsapi_search — urls={[s['url'] for s in signals]}")

        return signals

    except RuntimeError as e:
        logger.error(f"newsapi_search — CONFIG ERROR — {e}", exc_info=True)
        return []
    except NewsAPIException as e:
        logger.error(f"newsapi_search — NEWSAPI ERROR — {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"newsapi_search — ERROR — {e}", exc_info=True)
        return []