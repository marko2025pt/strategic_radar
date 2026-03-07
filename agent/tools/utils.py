# Version 1.1 — Final demo delivery to Ironhack 2026-03-06
"""
agent/tools/utils.py

Shared utilities for all Strategic Radar tools.

Contains:
- Shared FastMCP instance — imported by all tool files
- _classify_source() — URL-based source quality classifier
- Domain lists loaded from domain_lists.json

Design decision:
    Shared utilities live here, not inside individual tool files.
    Each tool imports from this module — tools have no dependencies
    on each other.

Post-MVP:
    domain_lists.json can be edited without touching code.
    Could be made editable via Gradio UI (see product_backlog.md RAG-3).
"""

import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from core.logging_config import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Shared FastMCP instance
# All tools register with this single instance.
# ---------------------------------------------------------------------------

mcp = FastMCP("strategic-radar")


# ---------------------------------------------------------------------------
# Domain lists loader
# ---------------------------------------------------------------------------

def _load_domain_lists() -> dict:
    """
    Loads primary and secondary domain lists from domain_lists.json.
    Falls back to empty lists if file is missing — classification
    will return 'unknown' for all domains rather than crashing.
    """
    domain_lists_path = Path(__file__).parent / "domain_lists.json"

    try:
        with open(domain_lists_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.debug(
            f"Loaded domain lists — "
            f"{len(data.get('primary', []))} primary, "
            f"{len(data.get('secondary', []))} secondary"
        )
        return data
    except FileNotFoundError:
        logger.warning(
            f"domain_lists.json not found at {domain_lists_path} — "
            f"all sources will be classified as 'unknown'"
        )
        return {"primary": [], "secondary": []}
    except json.JSONDecodeError as e:
        logger.error(
            f"domain_lists.json is not valid JSON: {e} — "
            f"all sources will be classified as 'unknown'"
        )
        return {"primary": [], "secondary": []}


# Load once at module import — not on every function call
_domain_lists = _load_domain_lists()


# ---------------------------------------------------------------------------
# Source classifier
# ---------------------------------------------------------------------------

def _classify_source(url: str) -> str:
    """
    Classifies a source URL as primary, secondary, or unknown.

    Primary:   company own domains, press release wires
    Secondary: industry publications, trade press, news aggregators
    Unknown:   everything else

    Args:
        url: Full URL string from any tool result.

    Returns:
        "primary" | "secondary" | "unknown"
    """
    if not url:
        return "unknown"

    url_lower = url.lower()

    for domain in _domain_lists.get("primary", []):
        if domain in url_lower:
            return "primary"

    for domain in _domain_lists.get("secondary", []):
        if domain in url_lower:
            return "secondary"

    return "unknown"