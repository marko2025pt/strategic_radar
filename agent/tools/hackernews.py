"""
agent/tools/hackernews.py

Hacker News search tool for the Strategic Radar agent.

Hacker News is used for technology signal discovery — it surfaces
emerging technology discussions, product launches, and industry
reactions that don't appear in traditional news APIs.

Uses the Algolia HN Search API — faster and more flexible than
the official Firebase API for keyword search.

No API key required. Free. No rate limit documented.

MCP integration: in-process using @mcp.tool() decorator.
Shared FastMCP instance and utilities imported from utils.py.
"""

import requests
from datetime import datetime, timedelta
from core.logging_config import get_logger
from agent.tools.utils import mcp, _classify_source

logger = get_logger(__name__)

HN_SEARCH_URL = "http://hn.algolia.com/api/v1/search_by_date"


def _days_to_timestamp(days: int) -> int:
    """
    Converts a day count to a Unix timestamp for HN Algolia API filtering.
    """
    from_date = datetime.utcnow() - timedelta(days=days)
    return int(from_date.timestamp())


@mcp.tool()
def hackernews_search(query: str, time_range_days: int = 7) -> list[dict]:
    """
    Searches Hacker News for recent stories matching the query.

    Uses the Algolia HN Search API for full-text search with
    date filtering. Returns stories only (not comments).

    Args:
        query:           Search string to execute.
        time_range_days: How many days back to search (7, 14, or 30).

    Returns:
        List of RawSignal dicts. Empty list on failure.
    """
    logger.info(f"hackernews_search — query='{query}' | days={time_range_days}")

    try:
        timestamp = _days_to_timestamp(time_range_days)

        params = {
            "query":          query,
            "tags":           "story",
            "numericFilters": f"created_at_i>{timestamp}",
            "hitsPerPage":    5,
        }

        response = requests.get(HN_SEARCH_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        hits = data.get("hits", [])
        signals = []

        for h in hits:
            url = h.get("url", "")

            # Some HN stories have no external URL (Ask HN, Show HN)
            # Use HN thread URL as fallback
            if not url:
                object_id = h.get("objectID", "")
                url = f"https://news.ycombinator.com/item?id={object_id}"

            title = h.get("title", "") or ""
            points = h.get("points", 0) or 0
            comments = h.get("num_comments", 0) or 0
            snippet = f"{title} — {points} points, {comments} comments on Hacker News"

            created_at = h.get("created_at", "")

            signal = {
                "title":        title,
                "url":          url,
                "snippet":      snippet,
                "source":       "news.ycombinator.com",
                "published_at": created_at,
                "source_type":  _classify_source(url),
                "api_origin":   "hackernews",
            }
            signals.append(signal)

        logger.info(f"hackernews_search — OK — returned {len(signals)} signals")
        logger.debug(f"hackernews_search — urls={[s['url'] for s in signals]}")

        return signals

    except requests.exceptions.Timeout:
        logger.warning(f"hackernews_search — TIMEOUT — query='{query}'")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"hackernews_search — REQUEST ERROR — {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"hackernews_search — ERROR — {e}", exc_info=True)
        return []