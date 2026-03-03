"""
agent/state.py

LangGraph state schema for the Strategic Radar agent.

This TypedDict is the single shared data structure that flows through
every node in the graph. Each node reads from it and writes back to it.
No node creates its own local state — everything lives here.

Design principles:
- Simple overwrite per node — no reducers
- Every field has a default — no node should ever receive a missing key
- Fields are ordered by pipeline stage for readability
- Optional fields use None as default — never assume presence downstream

Pipeline stages reflected in field order:
  1. Input          — what came in from the user / N8N
  2. Validation     — registry check results
  3. Query Building — constructed search strings
  4. Collection     — raw signals from APIs
  5. Selection      — top 5 signals chosen by LLM
  6. Evaluation     — RAG-grounded per-signal analysis
  7. Output         — final executive brief
  8. Meta           — run tracking and error handling
"""

from typing import TypedDict, Optional


# ---------------------------------------------------------------------------
# Signal dict shapes — documented here for reference
# ---------------------------------------------------------------------------

# RawSignal (stored in raw_signals):
# {
#   "title":        str   — headline or page title
#   "url":          str   — source URL
#   "snippet":      str   — summary or excerpt
#   "source":       str   — domain name (e.g. "reuters.com")
#   "published_at": str   — ISO date string or empty string
#   "source_type":  str   — "primary" | "secondary" | "unknown"
#   "api_origin":   str   — "tavily" | "newsapi" | "hackernews"
# }

# SelectedSignal (stored in selected_signals):
# {
#   "title":            str
#   "url":              str
#   "snippet":          str
#   "source":           str
#   "published_at":     str
#   "source_type":      str
#   "api_origin":       str
#   "selection_reason": str  — LLM's one-line reason for selecting this signal
# }

# EvaluatedSignal (stored in evaluated_signals):
# {
#   "title":            str
#   "url":              str
#   "snippet":          str
#   "source":           str
#   "published_at":     str
#   "source_type":      str
#   "api_origin":       str
#   "selection_reason": str
#   "impact_level":     str   — "High" | "Medium" | "Low"
#   "impact_summary":   str   — 2-3 sentence evaluation
#   "strategic_link":   str   — which objective(s) this maps to
#   "rag_score":        float — top Pinecone similarity score (0.0–1.0)
#   "confidence":       float — final confidence score (0.0–10.0)
# }


# ---------------------------------------------------------------------------
# AgentState
# ---------------------------------------------------------------------------

class AgentState(TypedDict):

    # ------------------------------------------------------------------
    # 1. INPUT
    # ------------------------------------------------------------------

    competitor: str
    # Competitor name — must match an entry in the competitor registry.
    # Example: "JCDecaux"

    intelligence_type: str
    # V1.0: "Competitor Moves"
    # V1.1 adds: "Business Opportunities"
    # V1.2 adds: "Technology Developments"

    time_range_days: int
    # How many days back to search. Accepted values: 7 | 14 | 30

    # ------------------------------------------------------------------
    # 2. VALIDATION
    # ------------------------------------------------------------------

    validated: bool
    # True → continue graph. False → route to END with error.

    competitor_profile: Optional[dict]
    # Full competitor entry from competitor_registry.json.
    # None if validation failed.
    # Keys: id, name, country, why_we_monitor, primary_domain

    # ------------------------------------------------------------------
    # 3. QUERY BUILDING
    # ------------------------------------------------------------------

    search_queries: list[str]
    # Search strings built deterministically from competitor + time window.
    # No LLM involved.
    # Example: ["JCDecaux DOOH 2025", "JCDecaux digital signage expansion"]

    # ------------------------------------------------------------------
    # 4. SIGNAL COLLECTION
    # ------------------------------------------------------------------

    raw_signals: list[dict]
    # All signals returned by Tavily, NewsAPI, and Hacker News.
    # Each dict follows RawSignal shape above.
    # May contain duplicates — deduplication happens in selection.
    # Empty list if all APIs failed.

    # ------------------------------------------------------------------
    # 5. STRATEGIC SELECTION
    # ------------------------------------------------------------------

    selected_signals: list[dict]
    # Top signals chosen by LLM from raw_signals. Maximum 5.
    # Each dict follows SelectedSignal shape above.
    # Empty list if raw_signals was empty.

    # ------------------------------------------------------------------
    # 6. SIGNAL EVALUATION
    # ------------------------------------------------------------------

    evaluated_signals: list[dict]
    # RAG-grounded evaluation of each selected signal.
    # One entry per selected signal, maximum 5.
    # Each dict follows EvaluatedSignal shape above.

    # ------------------------------------------------------------------
    # 7. OUTPUT
    # ------------------------------------------------------------------

    final_brief: Optional[str]
    # The 1-page executive snapshot as a formatted string.
    # None if the run failed before reaching brief generation.
    # Structure:
    #   Strategic Snapshot — {competitor} (Last {N} Days)
    #   High Impact / Medium Impact / Low Impact sections
    #   Confidence score per signal (0.0–10.0)
    #   Executive Takeaway (3-4 sentences)

    # ------------------------------------------------------------------
    # 8. META
    # ------------------------------------------------------------------

    run_id: str
    # Unique run identifier for log correlation.
    # Example: "run_20260303_161532_jcdecaux"

    error: Optional[str]
    # Human-readable error message. None if run completed without errors.
    # Set by validate node on invalid input.
    # Set by any node that catches an unrecoverable failure.

    llm_calls_made: int
    # Running count of LLM calls. Hard cap is 7 for V1.0.
    # Incremented by each node that calls the LLM.


# ---------------------------------------------------------------------------
# Default state factory
# ---------------------------------------------------------------------------

def default_state(
    competitor: str,
    intelligence_type: str,
    time_range_days: int,
    run_id: str,
) -> AgentState:
    """
    Returns a fully initialised AgentState with safe defaults.
    Call this at the entry point before invoking the graph.
    """
    if not competitor or not isinstance(competitor, str):
        raise ValueError(f"competitor must be a non-empty string, got: {repr(competitor)}")
    if time_range_days not in (7, 14, 30):
        raise ValueError(f"time_range_days must be 7, 14, or 30, got: {time_range_days}")

    return AgentState(
        # Input
        competitor=competitor,
        intelligence_type=intelligence_type,
        time_range_days=time_range_days,

        # Validation
        validated=False,
        competitor_profile=None,

        # Query building
        search_queries=[],

        # Collection
        raw_signals=[],

        # Selection
        selected_signals=[],

        # Evaluation
        evaluated_signals=[],

        # Output
        final_brief=None,

        # Meta
        run_id=run_id,
        error=None,
        llm_calls_made=0,
    )