"""
agent/nodes.py

Node implementations for the Strategic Radar LangGraph workflow.

Each node is a function that:
- Receives the full AgentState
- Does exactly one job
- Returns a dict of only the fields it updates

Nodes never modify state directly — they return changes and LangGraph
merges them. Nodes never raise unhandled exceptions — they catch errors,
log them, and return a safe state update so the graph can continue or
terminate gracefully.

Node registry (V1.0):
    validate         — registry check, no LLM
    build_queries    — query construction, no LLM
    collect_signals  — ReAct agent loop (Tavily + NewsAPI + HackerNews)
    select_signals   — 1 LLM call, picks top 5 signals
    evaluate_signals — up to 5 LLM + RAG calls, per-signal evaluation
    generate_brief   — 1 LLM call, produces final executive snapshot
"""

import json
from pathlib import Path
from agent.state import AgentState
from core.logging_config import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Registry loader — used by validate node
# ---------------------------------------------------------------------------

def _load_competitor_registry() -> dict:
    """
    Loads competitor_registry.json from the kb directory.
    Returns a dict keyed by lowercase competitor name for easy lookup.
    Raises RuntimeError if the file cannot be loaded.
    """
    registry_path = Path(__file__).parent.parent / "rag" / "kb" / "competitor_registry.json"

    try:
        with open(registry_path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        # Build lookup dict keyed by lowercase name
        # Supports both list format and dict format in the JSON
        registry = {}
        entries = raw if isinstance(raw, list) else raw.get("competitors", [])
        for entry in entries:
            key = entry["name"].lower()
            registry[key] = entry

        logger.debug(f"Loaded competitor registry — {len(registry)} entries")
        return registry

    except FileNotFoundError:
        raise RuntimeError(f"Competitor registry not found at: {registry_path}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Competitor registry is not valid JSON: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to load competitor registry: {e}") from e


# ---------------------------------------------------------------------------
# Valid intelligence types and time ranges — used by validate node
# ---------------------------------------------------------------------------

VALID_INTELLIGENCE_TYPES = {
    "Competitor Moves",       # V1.0
    # "Business Opportunities", # V1.1
    # "Technology Developments" # V1.2
}

VALID_TIME_RANGES = {7, 14, 30}


# ---------------------------------------------------------------------------
# Node 1 — validate
# ---------------------------------------------------------------------------

def validate(state: AgentState) -> dict:
    """
    Validates the incoming request against the competitor registry.

    Checks:
    - competitor exists in the registry
    - intelligence_type is supported in this version
    - time_range_days is one of the accepted values

    Returns:
        validated=True  + competitor_profile if all checks pass
        validated=False + error message if any check fails

    No LLM call. No API call. Deterministic.
    """
    try:
        logger.info(
            f"[{state['run_id']}] validate — start — "
            f"competitor='{state['competitor']}' | "
            f"type='{state['intelligence_type']}' | "
            f"days={state['time_range_days']}"
        )

        competitor_name = state["competitor"].strip()
        intelligence_type = state["intelligence_type"].strip()
        time_range_days = state["time_range_days"]

        # --- Check intelligence type ---
        if intelligence_type not in VALID_INTELLIGENCE_TYPES:
            msg = (
                f"intelligence_type '{intelligence_type}' is not supported in V1.0. "
                f"Supported: {sorted(VALID_INTELLIGENCE_TYPES)}"
            )
            logger.warning(f"[{state['run_id']}] validate — FAILED — {msg}")
            return {"validated": False, "error": msg}

        # --- Check time range ---
        if time_range_days not in VALID_TIME_RANGES:
            msg = (
                f"time_range_days '{time_range_days}' is not valid. "
                f"Accepted values: {sorted(VALID_TIME_RANGES)}"
            )
            logger.warning(f"[{state['run_id']}] validate — FAILED — {msg}")
            return {"validated": False, "error": msg}

        # --- Check competitor registry ---
        try:
            registry = _load_competitor_registry()
        except RuntimeError as e:
            msg = f"Could not load competitor registry: {e}"
            logger.error(f"[{state['run_id']}] validate — ERROR — {msg}", exc_info=True)
            return {"validated": False, "error": msg}

        competitor_key = competitor_name.lower()
        if competitor_key not in registry:
            available = sorted(registry.keys())
            msg = (
                f"Competitor '{competitor_name}' not found in registry. "
                f"Available: {available}"
            )
            logger.warning(f"[{state['run_id']}] validate — FAILED — {msg}")
            return {"validated": False, "error": msg}

        # --- All checks passed ---
        competitor_profile = registry[competitor_key]
        logger.info(
            f"[{state['run_id']}] validate — OK — "
            f"competitor='{competitor_name}'"
        )

        return {
            "validated": True,
            "competitor_profile": competitor_profile,
            "error": None,
        }

    except Exception as e:
        msg = f"Unexpected error in validate: {e}"
        logger.error(
            f"[{state['run_id']}] validate — UNEXPECTED ERROR — {msg}",
            exc_info=True
        )
        return {"validated": False, "error": msg}
    
    # ---------------------------------------------------------------------------
# Node 2 — build_queries
# ---------------------------------------------------------------------------

def build_queries(state: AgentState) -> dict:
    """
    Builds search query strings for the signal collection tools.

    Deterministic — no LLM, no API calls.
    Constructs queries from competitor name, known aliases/keywords
    from the competitor profile, and the time window.

    Returns:
        search_queries: list of strings ready to pass to tools
    """
    try:
        logger.info(
            f"[{state['run_id']}] build_queries — start — "
            f"competitor='{state['competitor']}'"
        )

        competitor = state["competitor"].strip()
        profile = state["competitor_profile"]
        days = state["time_range_days"]

        # --- Build time context string ---
        time_context = f"last {days} days" if days <= 14 else f"last {days} days"

        # --- Pull domain keywords from profile if available ---
        # These enrich queries beyond just the competitor name
        industry_keywords = []
        if profile:
            # Use why_we_monitor field to extract context if present
            why = profile.get("why_we_monitor", "")
            # Add country for geo-specific searches
            country = profile.get("country", "")
            if country:
                industry_keywords.append(country)

        # --- Core query templates ---
        # Each query targets a different signal type
        queries = [
            # General news
            f"{competitor} news {time_context}",

            # Strategy and expansion
            f"{competitor} strategy expansion announcement",

            # Product and technology
            f"{competitor} product launch technology innovation",

            # Partnerships and contracts
            f"{competitor} partnership contract win deal",

            # DOOH and kiosk industry context
            f"{competitor} digital signage kiosk DOOH",
        ]

        # --- Add country-specific query if available ---
        if industry_keywords:
            queries.append(f"{competitor} {' '.join(industry_keywords)} market")

        logger.info(
            f"[{state['run_id']}] build_queries — OK — "
            f"built {len(queries)} queries"
        )
        logger.debug(
            f"[{state['run_id']}] build_queries — queries={queries}"
        )

        return {"search_queries": queries}

    except Exception as e:
        msg = f"Unexpected error in build_queries: {e}"
        logger.error(
            f"[{state['run_id']}] build_queries — UNEXPECTED ERROR — {msg}",
            exc_info=True
        )
        # Return empty queries — collect_signals will handle empty gracefully
        return {"search_queries": [], "error": msg}

        # ---------------------------------------------------------------------------
# Node 3 — collect_signals (ReAct agent loop)
# ---------------------------------------------------------------------------

def collect_signals(state: AgentState) -> dict:
    """
    Collects raw signals from Tavily, NewsAPI, and Hacker News
    using a LangGraph ReAct agent loop.

    The ReAct agent reasons about which queries to run, executes
    the tools, observes results, and decides when enough signals
    have been collected. This is the only node with dynamic
    reasoning — all other nodes are deterministic or single LLM calls.

    Returns:
        raw_signals: deduplicated list of RawSignal dicts
    """
    try:
        logger.info(
            f"[{state['run_id']}] collect_signals — start — "
            f"{len(state['search_queries'])} queries available"
        )

        from dotenv import load_dotenv
        load_dotenv(override=True)

        from langchain_openai import ChatOpenAI
        from langchain_core.tools import tool as lc_tool
        from langgraph.prebuilt import create_react_agent
        from agent.tools.tavily import tavily_search
        from agent.tools.newsapi import newsapi_search
        from agent.tools.hackernews import hackernews_search

        # --- Wrap tools for LangChain ReAct agent ---
        @lc_tool
        def search_web(query: str) -> list[dict]:
            """Search the web for recent news and articles about a competitor."""
            return tavily_search(query, state["time_range_days"])

        @lc_tool
        def search_news(query: str) -> list[dict]:
            """Search news articles about a competitor."""
            return newsapi_search(query, state["time_range_days"])

        @lc_tool
        def search_hackernews(query: str) -> list[dict]:
            """Search Hacker News for technology signals related to a competitor."""
            return hackernews_search(query, state["time_range_days"])

        tools = [search_web, search_news, search_hackernews]

        # --- Initialise LLM ---
        llm = ChatOpenAI(model="gpt-4o", temperature=0)

        # --- Build ReAct agent ---
        agent = create_react_agent(llm, tools)

        # --- Build prompt ---
        competitor = state["competitor"]
        queries = state["search_queries"]
        days = state["time_range_days"]

        prompt = f"""You are a competitive intelligence researcher.

Your task is to find recent market signals about {competitor} from the last {days} days.

Use the available search tools to find relevant signals. You have these suggested queries:
{chr(10).join(f'- {q}' for q in queries)}

Instructions:
- Use search_web for general web search
- Use search_news for news articles
- Use search_hackernews for technology signals
- Run at least one query with each tool
- Stop when you have collected signals from all three tools
- Do not repeat the same query twice

Return all signals you found as a summary."""

        # --- Run ReAct agent ---
        logger.info(f"[{state['run_id']}] collect_signals — running ReAct agent")

        agent_response = agent.invoke({
            "messages": [{"role": "user", "content": prompt}]
        })

        # --- Extract tool results from message history ---
        raw_signals = []
        seen_urls = set()

        messages = agent_response.get("messages", [])
        for message in messages:
            # Tool results are ToolMessage instances
            if hasattr(message, "content") and hasattr(message, "name"):
                try:
                    import json as _json
                    content = message.content
                    if isinstance(content, str):
                        parsed = _json.loads(content)
                        if isinstance(parsed, list):
                            for signal in parsed:
                                url = signal.get("url", "")
                                if url and url not in seen_urls:
                                    seen_urls.add(url)
                                    raw_signals.append(signal)
                except Exception:
                    # Not JSON or not a signal list — skip
                    pass

        logger.info(
            f"[{state['run_id']}] collect_signals — OK — "
            f"{len(raw_signals)} deduplicated signals collected"
        )

        return {"raw_signals": raw_signals}

    except Exception as e:
        msg = f"Unexpected error in collect_signals: {e}"
        logger.error(
            f"[{state['run_id']}] collect_signals — UNEXPECTED ERROR — {msg}",
            exc_info=True
        )
        return {"raw_signals": [], "error": msg}


        # ---------------------------------------------------------------------------
# Node 4 — select_signals (1 LLM call)
# ---------------------------------------------------------------------------

def select_signals(state: AgentState) -> dict:
    """
    Selects the top 5 most strategically relevant signals from raw_signals.

    One LLM call. No RAG. The LLM looks at all raw signals and picks
    the ones most worth evaluating based on strategic relevance to
    the DOOH and kiosk industry.

    Returns:
        selected_signals: list of up to 5 SelectedSignal dicts
        llm_calls_made:   incremented by 1
    """
    try:
        logger.info(
            f"[{state['run_id']}] select_signals — start — "
            f"{len(state['raw_signals'])} raw signals to evaluate"
        )

        # --- Handle empty input gracefully ---
        if not state["raw_signals"]:
            logger.warning(
                f"[{state['run_id']}] select_signals — "
                f"no raw signals to select from"
            )
            return {
                "selected_signals": [],
                "llm_calls_made": state["llm_calls_made"],
            }

        from dotenv import load_dotenv
        load_dotenv(override=True)

        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = ChatOpenAI(model="gpt-4o", temperature=0)

        # --- Build signal list for prompt ---
        signals_text = ""
        for i, s in enumerate(state["raw_signals"], 1):
            signals_text += f"""
Signal {i}:
  Title:      {s.get('title', '')}
  URL:        {s.get('url', '')}
  Snippet:    {s.get('snippet', '')[:300]}
  Source:     {s.get('source', '')}
  Published:  {s.get('published_at', '')}
  API Origin: {s.get('api_origin', '')}
"""

        system_prompt = """You are a strategic intelligence analyst specialising in the 
DOOH (Digital Out-of-Home) and self-service kiosk industry.

Your task is to select the most strategically relevant signals from a list of raw search results.

You must return a JSON array. Each item must have exactly these fields:
- title: string
- url: string  
- snippet: string
- source: string
- published_at: string
- source_type: string
- api_origin: string
- selection_reason: string (one sentence explaining why this signal matters strategically)

Rules:
- Select maximum 5 signals
- Prioritise signals about: partnerships, acquisitions, product launches, 
  market expansion, technology innovation, major contracts
- Exclude: generic blog posts, job listings, unrelated content
- Return ONLY the JSON array, no other text, no markdown backticks"""

        user_prompt = f"""Select the most strategically relevant signals from this list.
Company being monitored: {state['competitor']}
Industry context: DOOH and self-service kiosk ecosystem

{signals_text}

Return a JSON array of the top signals with selection_reason for each."""

        # --- LLM call ---
        logger.info(f"[{state['run_id']}] select_signals — calling LLM")

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])

        llm_calls_made = state["llm_calls_made"] + 1

        # --- Parse response ---
        try:
            content = response.content.strip()
            # Strip markdown backticks if present
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0]

            selected = json.loads(content)

            if not isinstance(selected, list):
                raise ValueError("LLM did not return a JSON array")

            # Cap at 5
            selected = selected[:5]

            # Ensure all required fields are present
            required_fields = {
                "title", "url", "snippet", "source",
                "published_at", "source_type", "api_origin", "selection_reason"
            }
            clean_selected = []
            for item in selected:
                for field in required_fields:
                    if field not in item:
                        item[field] = ""
                clean_selected.append(item)

            logger.info(
                f"[{state['run_id']}] select_signals — OK — "
                f"selected {len(clean_selected)} signals | "
                f"llm_calls={llm_calls_made}"
            )

            return {
                "selected_signals": clean_selected,
                "llm_calls_made": llm_calls_made,
            }

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(
                f"[{state['run_id']}] select_signals — PARSE ERROR — {e}",
                exc_info=True
            )
            # Fall back to returning raw signals as selected
            fallback = []
            for s in state["raw_signals"][:5]:
                s["selection_reason"] = "Fallback — LLM parse error"
                fallback.append(s)
            return {
                "selected_signals": fallback,
                "llm_calls_made": llm_calls_made,
            }

    except Exception as e:
        msg = f"Unexpected error in select_signals: {e}"
        logger.error(
            f"[{state['run_id']}] select_signals — UNEXPECTED ERROR — {msg}",
            exc_info=True
        )
        return {
            "selected_signals": [],
            "llm_calls_made": state["llm_calls_made"],
            "error": msg,
        }
    
    # ---------------------------------------------------------------------------
# Node 5 — evaluate_signals (up to 5 LLM + RAG calls)
# ---------------------------------------------------------------------------

def evaluate_signals(state: AgentState) -> dict:
    """
    Evaluates each selected signal against the company's strategic
    identity and objectives using RAG-grounded LLM calls.

    One LLM call per signal. Maximum 5 calls.
    Each call retrieves relevant context from Pinecone before
    asking the LLM to evaluate strategic impact.

    Confidence score per signal:
        confidence = (rag_score * 0.6) + (source_quality * 0.4)
        Scaled to 0-10.

    Returns:
        evaluated_signals: list of EvaluatedSignal dicts
        llm_calls_made:    incremented by number of signals evaluated
    """
    try:
        logger.info(
            f"[{state['run_id']}] evaluate_signals — start — "
            f"{len(state['selected_signals'])} signals to evaluate"
        )

        # --- Handle empty input gracefully ---
        if not state["selected_signals"]:
            logger.warning(
                f"[{state['run_id']}] evaluate_signals — "
                f"no selected signals to evaluate"
            )
            return {
                "evaluated_signals": [],
                "llm_calls_made": state["llm_calls_made"],
            }

        from dotenv import load_dotenv
        load_dotenv(override=True)

        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage, SystemMessage
        from rag.retriever import retrieve

        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        llm_calls_made = state["llm_calls_made"]
        evaluated_signals = []

        # --- Source quality lookup for confidence scoring ---
        source_quality_map = {
            "primary":   1.0,
            "secondary": 0.6,
            "unknown":   0.3,
        }

        system_prompt = """You are a strategic intelligence analyst for PARTTEAM & OEMKIOSKS,
a Portuguese company specialising in DOOH digital signage and self-service kiosks.

You will be given:
1. A market signal about a competitor
2. Relevant context from the company's strategic knowledge base

Your task is to evaluate whether this signal matters to PARTTEAM & OEMKIOSKS and why.

You must return a JSON object with exactly these fields:
- impact_level: "High" | "Medium" | "Low"
- impact_summary: string (2-3 sentences explaining the impact)
- strategic_link: string (which objective or business area this maps to)

Rules for impact_level:
- High: directly threatens or enables a strategic objective
- Medium: indirectly relevant, worth monitoring
- Low: minimal relevance, peripheral signal

Return ONLY the JSON object, no other text, no markdown backticks."""

        # --- Evaluate each signal ---
        for i, signal in enumerate(state["selected_signals"], 1):

            # Check LLM call budget
            if llm_calls_made >= 6:
                logger.warning(
                    f"[{state['run_id']}] evaluate_signals — "
                    f"LLM call budget reached at signal {i}, stopping"
                )
                break

            logger.info(
                f"[{state['run_id']}] evaluate_signals — "
                f"evaluating signal {i}/{len(state['selected_signals'])}: "
                f"'{signal.get('title', '')[:60]}'"
            )

            # --- RAG retrieval ---
            try:
                rag_chunks = retrieve(
                    query=f"{signal.get('title', '')} {signal.get('snippet', '')}",
                    top_k=3,
                )
                rag_score = rag_chunks[0]["score"] if rag_chunks else 0.0
                rag_context = "\n\n".join([
                    f"[{c['chunk_type'].upper()} — {c['heading']}]\n{c['text']}"
                    for c in rag_chunks
                ])
            except Exception as e:
                logger.error(
                    f"[{state['run_id']}] evaluate_signals — "
                    f"RAG retrieval failed for signal {i}: {e}",
                    exc_info=True
                )
                rag_score = 0.0
                rag_context = "No strategic context available."

            # --- Build evaluation prompt ---
            user_prompt = f"""Evaluate this competitor signal:

COMPETITOR: {state['competitor']}
SIGNAL TITLE: {signal.get('title', '')}
SIGNAL SNIPPET: {signal.get('snippet', '')[:500]}
SOURCE: {signal.get('source', '')}
PUBLISHED: {signal.get('published_at', '')}
SELECTION REASON: {signal.get('selection_reason', '')}

STRATEGIC CONTEXT FROM KNOWLEDGE BASE:
{rag_context}

Evaluate the strategic impact of this signal for PARTTEAM & OEMKIOSKS."""

            # --- LLM call ---
            try:
                response = llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ])
                llm_calls_made += 1

                # --- Parse response ---
                content = response.content.strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[1]
                    content = content.rsplit("```", 1)[0]

                evaluation = json.loads(content)

                # --- Calculate confidence score ---
                source_type = signal.get("source_type", "unknown")
                source_quality = source_quality_map.get(source_type, 0.3)
                confidence = round(
                    ((rag_score * 0.6) + (source_quality * 0.4)) * 10, 1
                )

                # --- Build evaluated signal ---
                evaluated = {
                    **signal,
                    "impact_level":   evaluation.get("impact_level", "Low"),
                    "impact_summary": evaluation.get("impact_summary", ""),
                    "strategic_link": evaluation.get("strategic_link", ""),
                    "rag_score":      round(rag_score, 4),
                    "confidence":     confidence,
                }
                evaluated_signals.append(evaluated)

                logger.info(
                    f"[{state['run_id']}] evaluate_signals — "
                    f"signal {i} done — "
                    f"impact={evaluated['impact_level']} | "
                    f"rag_score={rag_score:.4f} | "
                    f"confidence={confidence}"
                )

            except (json.JSONDecodeError, ValueError) as e:
                logger.error(
                    f"[{state['run_id']}] evaluate_signals — "
                    f"parse error on signal {i}: {e}",
                    exc_info=True
                )
                # Include signal with safe defaults
                evaluated_signals.append({
                    **signal,
                    "impact_level":   "Low",
                    "impact_summary": "Evaluation failed — parse error.",
                    "strategic_link": "Unknown",
                    "rag_score":      0.0,
                    "confidence":     0.0,
                })
                llm_calls_made += 1

            except Exception as e:
                logger.error(
                    f"[{state['run_id']}] evaluate_signals — "
                    f"LLM error on signal {i}: {e}",
                    exc_info=True
                )
                # Include signal with safe defaults
                evaluated_signals.append({
                    **signal,
                    "impact_level":   "Low",
                    "impact_summary": "Evaluation failed — LLM error.",
                    "strategic_link": "Unknown",
                    "rag_score":      0.0,
                    "confidence":     0.0,
                })

        logger.info(
            f"[{state['run_id']}] evaluate_signals — OK — "
            f"{len(evaluated_signals)} signals evaluated | "
            f"total llm_calls={llm_calls_made}"
        )

        return {
            "evaluated_signals": evaluated_signals,
            "llm_calls_made":    llm_calls_made,
        }

    except Exception as e:
        msg = f"Unexpected error in evaluate_signals: {e}"
        logger.error(
            f"[{state['run_id']}] evaluate_signals — UNEXPECTED ERROR — {msg}",
            exc_info=True
        )
        return {
            "evaluated_signals": [],
            "llm_calls_made":    state["llm_calls_made"],
            "error":             msg,
        }
    
    # ---------------------------------------------------------------------------
# Node 6 — generate_brief (1 LLM call)
# ---------------------------------------------------------------------------

def generate_brief(state: AgentState) -> dict:
    """
    Generates the final 1-page executive strategic snapshot.

    One LLM call. Takes all evaluated signals, sorts by impact level,
    and produces a structured brief with confidence scores.

    Returns:
        final_brief:    formatted string ready for display or PDF
        llm_calls_made: incremented by 1
    """
    try:
        logger.info(
            f"[{state['run_id']}] generate_brief — start — "
            f"{len(state['evaluated_signals'])} evaluated signals"
        )

        from dotenv import load_dotenv
        load_dotenv(override=True)

        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        llm_calls_made = state["llm_calls_made"]

        # --- Handle empty input gracefully ---
        if not state["evaluated_signals"]:
            logger.warning(
                f"[{state['run_id']}] generate_brief — "
                f"no evaluated signals — generating empty brief"
            )
            brief = (
                f"Strategic Snapshot — {state['competitor']} "
                f"(Last {state['time_range_days']} Days)\n\n"
                f"No signals found for this competitor in the selected time window.\n\n"
                f"Executive Takeaway\n"
                f"No actionable intelligence was identified in this run. "
                f"Consider expanding the time window or checking back later."
            )
            return {
                "final_brief": brief,
                "llm_calls_made": llm_calls_made,
            }

        # --- Sort signals by impact level ---
        impact_order = {"High": 0, "Medium": 1, "Low": 2}
        sorted_signals = sorted(
            state["evaluated_signals"],
            key=lambda s: impact_order.get(s.get("impact_level", "Low"), 2)
        )

        # --- Build signals block for prompt ---
        signals_block = ""
        for s in sorted_signals:
            signals_block += f"""
---
Title:          {s.get('title', '')}
Impact Level:   {s.get('impact_level', '')}
Confidence:     {s.get('confidence', 0.0)}/10
Strategic Link: {s.get('strategic_link', '')}
Impact Summary: {s.get('impact_summary', '')}
Source:         {s.get('url', '')}
Published:      {s.get('published_at', '')}
"""

        system_prompt = """You are a strategic intelligence analyst writing a 1-page 
executive brief for the leadership team of PARTTEAM & OEMKIOSKS.

Your brief must be concise, professional, and immediately actionable.

Format the brief EXACTLY as follows:

Strategic Snapshot — {COMPETITOR} (Last {N} Days)

── HIGH IMPACT ──────────────────────────────────────
[List high impact signals here. For each:
  • Signal title — Confidence: X.X/10
    Impact: [impact_summary]
    Strategic Link: [strategic_link]
    Source: [url]
]

── MEDIUM IMPACT ────────────────────────────────────
[List medium impact signals here. Same format.]

── LOW IMPACT ───────────────────────────────────────
[List low impact signals here. Same format.]

── EXECUTIVE TAKEAWAY ───────────────────────────────
[3-4 sentences synthesising the overall picture. 
What is the key strategic message from these signals?
What should leadership pay attention to?]

Rules:
- If a section has no signals, write "No signals at this impact level."
- Keep impact summaries concise — 1-2 sentences max in the brief
- The Executive Takeaway must be actionable, not descriptive
- Do not add any text outside the format above"""

        user_prompt = f"""Generate the executive brief for:

Competitor: {state['competitor']}
Time Window: Last {state['time_range_days']} days
Run ID: {state['run_id']}

Evaluated Signals:
{signals_block}"""

        # --- LLM call ---
        logger.info(f"[{state['run_id']}] generate_brief — calling LLM")

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])

        llm_calls_made += 1
        final_brief = response.content.strip()

        logger.info(
            f"[{state['run_id']}] generate_brief — OK — "
            f"brief generated | total llm_calls={llm_calls_made}"
        )

        return {
            "final_brief":    final_brief,
            "llm_calls_made": llm_calls_made,
            "error":          None,
        }

    except Exception as e:
        msg = f"Unexpected error in generate_brief: {e}"
        logger.error(
            f"[{state['run_id']}] generate_brief — UNEXPECTED ERROR — {msg}",
            exc_info=True
        )
        # Always return something — surface error in brief
        fallback_brief = (
            f"Strategic Snapshot — {state['competitor']} "
            f"(Last {state['time_range_days']} Days)\n\n"
            f"Brief generation failed: {msg}\n\n"
            f"Please check logs for run_id: {state['run_id']}"
        )
        return {
            "final_brief":    fallback_brief,
            "llm_calls_made": state["llm_calls_made"],
            "error":          msg,
        }