
"""
agent/state.py  —  V1.1 updated

Changes from previous V1.1:
  - Added raw_pretender_signals: list[dict]
    Pre-tender public signals (budget approvals, council decisions, EU funds)
    Separated from raw_private_signals at collection time.
  - Added evaluated_pretender: list[dict]
    Evaluated pre-tender signals — positioning-focused evaluation.
"""

from typing import TypedDict, Optional


class AgentState(TypedDict):

    # ------------------------------------------------------------------
    # 1. INPUT
    # ------------------------------------------------------------------

    subject: str
    intelligence_type: str
    time_range_days: int
    sector: Optional[str]

    # ------------------------------------------------------------------
    # 2. VALIDATION
    # ------------------------------------------------------------------

    validated: bool
    competitor_profile: Optional[dict]

    # ------------------------------------------------------------------
    # 3. QUERY BUILDING
    # ------------------------------------------------------------------

    search_queries: list[str]

    # ------------------------------------------------------------------
    # 4. SIGNAL COLLECTION  (V1.0 — Competitor Moves)
    # ------------------------------------------------------------------

    raw_signals: list[dict]

    # ------------------------------------------------------------------
    # 4b. OPPORTUNITY COLLECTION  (V1.1 — Business Opportunities)
    # ------------------------------------------------------------------

    raw_tenders: list[dict]
    # Live EU public tenders from TED API.

    raw_private_signals: list[dict]
    # Private sector expansion signals — press releases, trade press,
    # investor announcements. Commercial sales motion.

    raw_pretender_signals: list[dict]
    # Pre-tender public signals — budget approvals, city council decisions,
    # EU fund allocations. Not on TED yet. 3-12 month positioning window.

    # ------------------------------------------------------------------
    # 5. STRATEGIC SELECTION  (V1.0)
    # ------------------------------------------------------------------

    selected_signals: list[dict]

    # ------------------------------------------------------------------
    # 6. SIGNAL EVALUATION  (V1.0)
    # ------------------------------------------------------------------

    evaluated_signals: list[dict]

    # ------------------------------------------------------------------
    # 6b. OPPORTUNITY EVALUATION  (V1.1)
    # ------------------------------------------------------------------

    evaluated_tenders: list[dict]
    evaluated_private: list[dict]

    evaluated_pretender: list[dict]
    # Evaluated pre-tender signals — positioning window, not immediate action.

    # ------------------------------------------------------------------
    # 7. OUTPUT
    # ------------------------------------------------------------------

    final_brief: Optional[str]

    # ------------------------------------------------------------------
    # 8. META
    # ------------------------------------------------------------------

    run_id: str
    error: Optional[str]
    llm_calls_made: int


# ---------------------------------------------------------------------------
# Default state factory
# ---------------------------------------------------------------------------

def default_state(
    subject: str,
    intelligence_type: str,
    time_range_days: int,
    run_id: str,
    sector: Optional[str] = None,
) -> AgentState:

    if not subject or not isinstance(subject, str):
        raise ValueError(f"subject must be a non-empty string, got: {repr(subject)}")
    if time_range_days not in (7, 14, 30):
        raise ValueError(f"time_range_days must be 7, 14, or 30, got: {time_range_days}")

    return AgentState(
        # Input
        subject=subject,
        intelligence_type=intelligence_type,
        time_range_days=time_range_days,
        sector=sector,

        # Validation
        validated=False,
        competitor_profile=None,

        # Query building
        search_queries=[],

        # V1.0 collection
        raw_signals=[],

        # V1.1 collection
        raw_tenders=[],
        raw_private_signals=[],
        raw_pretender_signals=[],

        # V1.0 selection + evaluation
        selected_signals=[],
        evaluated_signals=[],

        # V1.1 evaluation
        evaluated_tenders=[],
        evaluated_private=[],
        evaluated_pretender=[],

        # Output
        final_brief=None,

        # Meta
        run_id=run_id,
        error=None,
        llm_calls_made=0,
    )