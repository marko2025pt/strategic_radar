"""
agent/tools/tavily.py

Tavily web search tool for the Strategic Radar agent.

Tavily is the primary signal discovery tool — it performs real-time
web searches optimised for AI agents, returning clean snippets with
URLs and publication metadata.

MCP integration: in-process using @mcp.tool() decorator.
Shared FastMCP instance and utilities imported from utils.py.
"""

import os
from tavily import TavilyClient
from core.logging_config import get_logger
from agent.tools.utils import mcp, _classify_source

logger = get_logger(__name__)


def _get_client() -> TavilyClient:
    """
    Returns an authenticated Tavily client.
    Raises RuntimeError if API key is missing.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY is not set in environment")
    return TavilyClient(api_key=api_key)


@mcp.tool()
def tavily_search(query: str, time_range_days: int = 7) -> list[dict]:
    """
    Searches the web for recent news and articles using Tavily.

    Args:
        query:           Search string to execute.
        time_range_days: How many days back to search (7, 14, or 30).

    Returns:
        List of RawSignal dicts. Empty list on failure.
    """
    logger.info(f"tavily_search — query='{query}' | days={time_range_days}")

    try:
        client = _get_client()

        if time_range_days <= 7:
            days_param = 7
        elif time_range_days <= 14:
            days_param = 14
        else:
            days_param = 30

        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            days=days_param,
            include_answer=False,
        )

        results = response.get("results", [])
        signals = []

        for r in results:
            url = r.get("url", "")
            signal = {
                "title":        r.get("title", ""),
                "url":          url,
                "snippet":      r.get("content", ""),
                "source":       r.get("source", ""),
                "published_at": r.get("published_date", ""),
                "source_type":  _classify_source(url),
                "api_origin":   "tavily",
            }
            signals.append(signal)

        logger.info(f"tavily_search — OK — returned {len(signals)} signals")
        logger.debug(f"tavily_search — urls={[s['url'] for s in signals]}")

        return signals

    except RuntimeError as e:
        logger.error(f"tavily_search — CONFIG ERROR — {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"tavily_search — ERROR — {e}", exc_info=True)
        return []