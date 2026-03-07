# Version 1.1 — Final demo delivery to Ironhack 2026-03-06
"""
agent/nodes.py  —  V1.1 + fixes + dedup

Changes from V1.1:
  FIX 1 — Translation:
      tender_system prompt instructs LLM to return translated_title.
      _evaluate_item uses translated_title to overwrite item title.

  FIX 2 — Impact classification criteria:
      Explicit High/Medium/Low rubric added to all 4 system prompts
      (evaluate_signals, tender_system, private_system, pretender_system).

  FIX 3 — Irrelevant signal filtering:
      All 3 opportunity system prompts instruct LLM to return "Irrelevant"
      if signal has no realistic connection to PARTTEAM products.
      _evaluate_item drops "Irrelevant" items and returns None.

  FIX 4 — Confidence formula:
      Old: (rag_score * 0.6) + (source_quality * 0.4)
      New: (llm_score * 0.5) + (rag_score * 0.3) + (source_quality * 0.2)
      LLM returns relevance_score (1-10) in all evaluation JSON responses.

  FIX 5 — Deduplication:
      _is_duplicate_title() helper added above Node 3.
      Both collect_signals and collect_opportunities apply two-layer dedup
      in the message parsing loop:
        Layer 1 — URL exact match
        Layer 2 — title word-overlap (threshold = 4 meaningful words)

Full file — replace nodes.py entirely.
"""

import json
from pathlib import Path
from agent.state import AgentState
from core.logging_config import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Registry loader
# ---------------------------------------------------------------------------

def _load_competitor_registry() -> dict:
    registry_path = Path(__file__).parent.parent / "rag" / "kb" / "competitor_registry.json"
    try:
        with open(registry_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
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
# Valid values
# ---------------------------------------------------------------------------

VALID_INTELLIGENCE_TYPES = {
    "Competitor Moves",
    "Business Opportunities",
    # "Technology Developments",  # V1.2
}

VALID_TIME_RANGES = {7, 14, 30}

VALID_SECTORS = {
    "QSR and Food Service",
    "Smart Cities",
    "Airport and Transport",
    "Retail",
    "Public Services",
}


# ---------------------------------------------------------------------------
# FIX 5 — Dedup helper
# ---------------------------------------------------------------------------

def _is_duplicate_title(title: str, seen_titles: list[str], threshold: int = 4) -> bool:
    """
    Returns True if `title` shares >= threshold meaningful words with any seen title.
    Used only on small lists (< 20 items) so O(n) is fine.
    """
    stop = {
        "the","a","an","of","in","for","to","and","or","on","at","by",
        "with","is","are","its","as","that","this"
    }
    def words(t):
        return {w.lower().strip(".,:-") for w in t.split() if w.lower() not in stop}
    candidate = words(title)
    for seen in seen_titles:
        if len(candidate & words(seen)) >= threshold:
            return True
    return False


# ---------------------------------------------------------------------------
# Node 1 — validate
# ---------------------------------------------------------------------------

def validate(state: AgentState) -> dict:
    try:
        logger.info(
            f"[{state['run_id']}] validate — start — "
            f"subject='{state['subject']}' | "
            f"type='{state['intelligence_type']}' | "
            f"days={state['time_range_days']}"
        )

        subject           = state["subject"].strip()
        intelligence_type = state["intelligence_type"].strip()
        time_range_days   = state["time_range_days"]

        if intelligence_type not in VALID_INTELLIGENCE_TYPES:
            msg = (
                f"intelligence_type '{intelligence_type}' is not supported. "
                f"Supported: {sorted(VALID_INTELLIGENCE_TYPES)}"
            )
            logger.warning(f"[{state['run_id']}] validate — FAILED — {msg}")
            return {"validated": False, "error": msg}

        if time_range_days not in VALID_TIME_RANGES:
            msg = (
                f"time_range_days '{time_range_days}' is not valid. "
                f"Accepted: {sorted(VALID_TIME_RANGES)}"
            )
            logger.warning(f"[{state['run_id']}] validate — FAILED — {msg}")
            return {"validated": False, "error": msg}

        if intelligence_type == "Competitor Moves":
            try:
                registry = _load_competitor_registry()
            except RuntimeError as e:
                msg = f"Could not load competitor registry: {e}"
                logger.error(f"[{state['run_id']}] validate — ERROR — {msg}", exc_info=True)
                return {"validated": False, "error": msg}

            key = subject.lower()
            if key not in registry:
                available = sorted(registry.keys())
                msg = (
                    f"Competitor '{subject}' not found in registry. "
                    f"Available: {available}"
                )
                logger.warning(f"[{state['run_id']}] validate — FAILED — {msg}")
                return {"validated": False, "error": msg}

            logger.info(f"[{state['run_id']}] validate — OK — subject='{subject}'")
            return {
                "validated":          True,
                "competitor_profile": registry[key],
                "sector":             None,
                "error":              None,
            }

        if intelligence_type == "Business Opportunities":
            if subject not in VALID_SECTORS:
                msg = (
                    f"Sector '{subject}' not recognised. "
                    f"Valid sectors: {sorted(VALID_SECTORS)}"
                )
                logger.warning(f"[{state['run_id']}] validate — FAILED — {msg}")
                return {"validated": False, "error": msg}

            logger.info(f"[{state['run_id']}] validate — OK — sector='{subject}'")
            return {
                "validated":          True,
                "competitor_profile": None,
                "sector":             subject,
                "error":              None,
            }

        return {"validated": False, "error": f"Unhandled intelligence_type: {intelligence_type}"}

    except Exception as e:
        msg = f"Unexpected error in validate: {e}"
        logger.error(f"[{state['run_id']}] validate — UNEXPECTED ERROR — {msg}", exc_info=True)
        return {"validated": False, "error": msg}


# ---------------------------------------------------------------------------
# Node 2 — build_queries
# ---------------------------------------------------------------------------

def build_queries(state: AgentState) -> dict:
    try:
        logger.info(
            f"[{state['run_id']}] build_queries — start — "
            f"subject='{state['subject']}' | type='{state['intelligence_type']}'"
        )

        if state["intelligence_type"] == "Competitor Moves":
            subject = state["subject"].strip()
            profile = state["competitor_profile"]
            days    = state["time_range_days"]

            industry_keywords = []
            if profile:
                country = profile.get("country", "")
                if country:
                    industry_keywords.append(country)

            queries = [
                f"{subject} news last {days} days",
                f"{subject} strategy expansion announcement",
                f"{subject} product launch technology innovation",
                f"{subject} partnership contract win deal",
                f"{subject} digital signage kiosk DOOH",
            ]
            if industry_keywords:
                queries.append(f"{subject} {' '.join(industry_keywords)} market")

        else:
            sector = state["subject"]
            days   = state["time_range_days"]

            private_queries = {
                "QSR and Food Service": [
                    f"McDonald's new restaurant opening expansion {days} days",
                    f"Burger King KFC Subway new location rollout announcement",
                    f"fast food chain kiosk self-service rollout Europe",
                    f"QSR restaurant expansion franchise new sites press release",
                    f"quick service restaurant digital ordering kiosk contract",
                ],
                "Smart Cities": [
                    f"smart city digital infrastructure contract award {days} days",
                    f"city council digital signage wayfinding kiosk investment",
                    f"smart city technology rollout announcement Europe",
                    f"municipal digital transformation kiosk public display",
                    f"urban digital signage public information system contract",
                ],
                "Airport and Transport": [
                    f"airport terminal expansion digital signage kiosk contract",
                    f"train station transport hub self-service kiosk installation",
                    f"airport technology upgrade passenger information system",
                    f"transport operator kiosk digital signage announcement",
                    f"airport renovation terminal modernisation digital",
                ],
                "Retail": [
                    f"retail chain store expansion new location rollout announcement",
                    f"supermarket shopping mall self-service kiosk installation",
                    f"retail digital signage interactive display contract",
                    f"flagship store digital transformation kiosk technology",
                    f"retail expansion Europe new stores press release",
                ],
                "Public Services": [
                    f"government digital services kiosk self-service terminal",
                    f"public sector citizen digital service terminal contract",
                    f"hospital library municipality self-service kiosk rollout",
                    f"public service digitalisation kiosk investment announcement",
                    f"government digital transformation interactive terminal",
                ],
            }

            queries = private_queries.get(sector, [
                f"{sector} kiosk digital signage opportunity expansion",
                f"{sector} self-service technology contract announcement",
            ])

        logger.info(f"[{state['run_id']}] build_queries — OK — {len(queries)} queries")
        logger.debug(f"[{state['run_id']}] build_queries — queries={queries}")
        return {"search_queries": queries}

    except Exception as e:
        msg = f"Unexpected error in build_queries: {e}"
        logger.error(f"[{state['run_id']}] build_queries — UNEXPECTED ERROR — {msg}", exc_info=True)
        return {"search_queries": [], "error": msg}


# ---------------------------------------------------------------------------
# Node 3 — collect_signals  (V1.0 + FIX 5)
# ---------------------------------------------------------------------------

def collect_signals(state: AgentState) -> dict:
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
        llm   = ChatOpenAI(model="gpt-4o", temperature=0)
        agent = create_react_agent(llm, tools)

        subject = state["subject"]
        queries = state["search_queries"]
        days    = state["time_range_days"]

        prompt = f"""You are a competitive intelligence researcher.

Your task is to find recent market signals about {subject} from the last {days} days.

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

        logger.info(f"[{state['run_id']}] collect_signals — running ReAct agent")
        agent_response = agent.invoke({"messages": [{"role": "user", "content": prompt}]})

        # FIX 5 — two-layer dedup: URL exact match + title word-overlap
        raw_signals  = []
        seen_urls    = set()
        seen_titles  = []
        messages     = agent_response.get("messages", [])

        for message in messages:
            if hasattr(message, "content") and hasattr(message, "name"):
                try:
                    import json as _json
                    content = message.content
                    if isinstance(content, str):
                        parsed = _json.loads(content)
                        if isinstance(parsed, list):
                            for signal in parsed:
                                url   = signal.get("url", "").strip()
                                title = signal.get("title", "").strip()
                                if url and url in seen_urls:
                                    continue
                                if title and _is_duplicate_title(title, seen_titles):
                                    continue
                                if url:
                                    seen_urls.add(url)
                                if title:
                                    seen_titles.append(title)
                                raw_signals.append(signal)
                except Exception:
                    pass

        logger.info(
            f"[{state['run_id']}] collect_signals — OK — "
            f"{len(raw_signals)} signals after dedup"
        )
        return {"raw_signals": raw_signals}

    except Exception as e:
        msg = f"Unexpected error in collect_signals: {e}"
        logger.error(f"[{state['run_id']}] collect_signals — UNEXPECTED ERROR — {msg}", exc_info=True)
        return {"raw_signals": [], "error": msg}


# ---------------------------------------------------------------------------
# Node 4 — select_signals  (V1.0 — unchanged)
# ---------------------------------------------------------------------------

def select_signals(state: AgentState) -> dict:
    try:
        logger.info(
            f"[{state['run_id']}] select_signals — start — "
            f"{len(state['raw_signals'])} raw signals"
        )

        if not state["raw_signals"]:
            logger.warning(f"[{state['run_id']}] select_signals — no raw signals")
            return {"selected_signals": [], "llm_calls_made": state["llm_calls_made"]}

        from dotenv import load_dotenv
        load_dotenv(override=True)

        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = ChatOpenAI(model="gpt-4o", temperature=0)

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

Select the most strategically relevant signals. Return a JSON array with fields:
title, url, snippet, source, published_at, source_type, api_origin, selection_reason.
Select maximum 5. Return ONLY the JSON array, no markdown."""

        user_prompt = f"""Select the most strategically relevant signals.
Company context: PARTTEAM & OEMKIOSKS — DOOH and self-service kiosk ecosystem
Subject: {state['subject']}

{signals_text}

Return JSON array of top signals with selection_reason for each."""

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])
        llm_calls_made = state["llm_calls_made"] + 1

        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            selected = json.loads(content)
            if not isinstance(selected, list):
                raise ValueError("Not a JSON array")
            selected = selected[:5]
            required = {"title","url","snippet","source","published_at","source_type","api_origin","selection_reason"}
            clean = []
            for item in selected:
                for f in required:
                    if f not in item:
                        item[f] = ""
                clean.append(item)
            logger.info(f"[{state['run_id']}] select_signals — OK — {len(clean)} selected")
            return {"selected_signals": clean, "llm_calls_made": llm_calls_made}

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"[{state['run_id']}] select_signals — PARSE ERROR — {e}")
            fallback = []
            for s in state["raw_signals"][:5]:
                s["selection_reason"] = "Fallback — parse error"
                fallback.append(s)
            return {"selected_signals": fallback, "llm_calls_made": llm_calls_made}

    except Exception as e:
        msg = f"Unexpected error in select_signals: {e}"
        logger.error(f"[{state['run_id']}] select_signals — UNEXPECTED ERROR — {msg}", exc_info=True)
        return {"selected_signals": [], "llm_calls_made": state["llm_calls_made"], "error": msg}


# ---------------------------------------------------------------------------
# Node 5 — evaluate_signals  (V1.0 + FIX 2 + FIX 4)
# ---------------------------------------------------------------------------

def evaluate_signals(state: AgentState) -> dict:
    """
    FIX 2: Added explicit High/Medium/Low impact criteria to system prompt.
    FIX 4: Confidence now = (llm_score * 0.5) + (rag_score * 0.3) + (source_quality * 0.2)
           LLM returns relevance_score (1-10) as part of the JSON response.
    """
    try:
        logger.info(
            f"[{state['run_id']}] evaluate_signals — start — "
            f"{len(state['selected_signals'])} signals"
        )

        if not state["selected_signals"]:
            logger.warning(f"[{state['run_id']}] evaluate_signals — no signals")
            return {"evaluated_signals": [], "llm_calls_made": state["llm_calls_made"]}

        from dotenv import load_dotenv
        load_dotenv(override=True)

        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage, SystemMessage
        from rag.retriever import retrieve

        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        llm_calls_made     = state["llm_calls_made"]
        evaluated_signals  = []
        source_quality_map = {"primary": 1.0, "secondary": 0.6, "unknown": 0.3}

        system_prompt = """You are a strategic intelligence analyst for PARTTEAM & OEMKIOSKS,
a Portuguese company specialising in DOOH digital signage and self-service kiosks.

Given a market signal and strategic context from the knowledge base, evaluate
whether this signal matters to PARTTEAM & OEMKIOSKS and why.

Impact classification criteria:
- High: direct threat or opportunity requiring immediate strategic response
- Medium: relevant development to monitor and prepare for
- Low: background noise — interesting but no action required

Return a JSON object with exactly:
- impact_level: "High" | "Medium" | "Low"
- impact_summary: string (2-3 sentences)
- strategic_link: string (which objective or business area)
- relevance_score: integer 1-10 (your own assessment of strategic importance to PARTTEAM)

Return ONLY the JSON object, no markdown."""

        for i, signal in enumerate(state["selected_signals"], 1):
            if llm_calls_made >= 6:
                logger.warning(f"[{state['run_id']}] evaluate_signals — budget reached at {i}")
                break

            try:
                rag_chunks = retrieve(
                    query=f"{signal.get('title','')} {signal.get('snippet','')}",
                    top_k=3,
                )
                rag_score   = rag_chunks[0]["score"] if rag_chunks else 0.0
                rag_context = "\n\n".join([
                    f"[{c['chunk_type'].upper()} — {c['heading']}]\n{c['text']}"
                    for c in rag_chunks
                ])
            except Exception as e:
                logger.error(f"[{state['run_id']}] evaluate_signals — RAG error {i}: {e}")
                rag_score, rag_context = 0.0, "No strategic context available."

            user_prompt = f"""Evaluate this competitor signal:

COMPETITOR: {state['subject']}
SIGNAL TITLE: {signal.get('title','')}
SIGNAL SNIPPET: {signal.get('snippet','')[:500]}
SOURCE: {signal.get('source','')}
PUBLISHED: {signal.get('published_at','')}

STRATEGIC CONTEXT:
{rag_context}

Evaluate strategic impact for PARTTEAM & OEMKIOSKS."""

            try:
                response = llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ])
                llm_calls_made += 1
                content = response.content.strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[1].rsplit("```", 1)[0]
                evaluation = json.loads(content)

                llm_score      = evaluation.get("relevance_score", 5) / 10
                source_quality = source_quality_map.get(signal.get("source_type", "unknown"), 0.3)
                confidence     = round(
                    ((llm_score * 0.5) + (rag_score * 0.3) + (source_quality * 0.2)) * 10, 1
                )

                evaluated_signals.append({
                    **signal,
                    "impact_level":    evaluation.get("impact_level", "Low"),
                    "impact_summary":  evaluation.get("impact_summary", ""),
                    "strategic_link":  evaluation.get("strategic_link", ""),
                    "relevance_score": evaluation.get("relevance_score", 5),
                    "rag_score":       round(rag_score, 4),
                    "confidence":      confidence,
                })
                logger.info(
                    f"[{state['run_id']}] evaluate_signals — signal {i} — "
                    f"impact={evaluation.get('impact_level')} | "
                    f"llm_score={evaluation.get('relevance_score')} | "
                    f"confidence={confidence}"
                )
            except Exception as e:
                logger.error(f"[{state['run_id']}] evaluate_signals — error {i}: {e}")
                evaluated_signals.append({
                    **signal,
                    "impact_level":    "Low",
                    "impact_summary":  "Evaluation failed.",
                    "strategic_link":  "Unknown",
                    "relevance_score": 0,
                    "rag_score":       0.0,
                    "confidence":      0.0,
                })

        logger.info(f"[{state['run_id']}] evaluate_signals — OK — {len(evaluated_signals)} evaluated")
        return {"evaluated_signals": evaluated_signals, "llm_calls_made": llm_calls_made}

    except Exception as e:
        msg = f"Unexpected error in evaluate_signals: {e}"
        logger.error(f"[{state['run_id']}] evaluate_signals — UNEXPECTED ERROR — {msg}", exc_info=True)
        return {"evaluated_signals": [], "llm_calls_made": state["llm_calls_made"], "error": msg}


# ---------------------------------------------------------------------------
# Node 6 — generate_brief  (V1.0 — unchanged)
# ---------------------------------------------------------------------------

def generate_brief(state: AgentState) -> dict:
    try:
        logger.info(f"[{state['run_id']}] generate_brief — start")

        from dotenv import load_dotenv
        load_dotenv(override=True)

        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        llm_calls_made = state["llm_calls_made"]

        if not state["evaluated_signals"]:
            brief = (
                f"Strategic Snapshot — {state['subject']} "
                f"(Last {state['time_range_days']} Days)\n\n"
                f"No signals found in the selected time window.\n\n"
                f"Executive Takeaway\nNo actionable intelligence identified. "
                f"Consider expanding the time window."
            )
            return {"final_brief": brief, "llm_calls_made": llm_calls_made}

        impact_order  = {"High": 0, "Medium": 1, "Low": 2}
        sorted_signals = sorted(
            state["evaluated_signals"],
            key=lambda s: impact_order.get(s.get("impact_level", "Low"), 2)
        )

        signals_block = ""
        for s in sorted_signals:
            signals_block += f"""
---
Title:          {s.get('title','')}
Impact Level:   {s.get('impact_level','')}
Confidence:     {s.get('confidence',0.0)}/10
Strategic Link: {s.get('strategic_link','')}
Impact Summary: {s.get('impact_summary','')}
Source:         {s.get('url','')}
Published:      {s.get('published_at','')}
"""

        system_prompt = """You are a strategic intelligence analyst writing a 1-page
executive brief for PARTTEAM & OEMKIOSKS leadership.

Format EXACTLY as:

Strategic Snapshot — {SUBJECT} (Last {N} Days)

── HIGH IMPACT ──────────────────────────────────────
[Each signal: • Title — Confidence: X.X/10 / Impact: ... / Strategic Link: ... / Source: url]

── MEDIUM IMPACT ────────────────────────────────────
[Same format]

── LOW IMPACT ───────────────────────────────────────
[Same format]

── EXECUTIVE TAKEAWAY ───────────────────────────────
[3-4 sentences. Actionable, not descriptive.]

If a section has no signals, write "No signals at this impact level."
Return ONLY the formatted brief, no other text."""

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Competitor: {state['subject']}\nTime: Last {state['time_range_days']} days\n\n{signals_block}"),
        ])
        llm_calls_made += 1

        logger.info(f"[{state['run_id']}] generate_brief — OK — llm_calls={llm_calls_made}")
        return {"final_brief": response.content.strip(), "llm_calls_made": llm_calls_made, "error": None}

    except Exception as e:
        msg = f"Unexpected error in generate_brief: {e}"
        logger.error(f"[{state['run_id']}] generate_brief — UNEXPECTED ERROR — {msg}", exc_info=True)
        fallback = (
            f"Strategic Snapshot — {state['subject']} (Last {state['time_range_days']} Days)\n\n"
            f"Brief generation failed: {msg}\nRun ID: {state['run_id']}"
        )
        return {"final_brief": fallback, "llm_calls_made": state["llm_calls_made"], "error": msg}


# ===========================================================================
# V1.1 NODES — Business Opportunities
# ===========================================================================


# ---------------------------------------------------------------------------
# Node 7 — collect_opportunities  (V1.1 + FIX 5)
# ---------------------------------------------------------------------------

def collect_opportunities(state: AgentState) -> dict:
    """
    Collects three types of business opportunity signals:
    1. Live EU public tenders (TED API — direct call, deterministic)
    2. Private sector expansion signals (Tavily + NewsAPI)
    3. Pre-tender public signals (Tavily + NewsAPI)

    FIX 5: Two-layer dedup applied in message parsing loop.
    """
    try:
        sector = state["sector"] or state["subject"]
        days   = state["time_range_days"]

        logger.info(
            f"[{state['run_id']}] collect_opportunities — start — "
            f"sector='{sector}' | days={days}"
        )

        from datetime import datetime
        from dotenv import load_dotenv
        load_dotenv(override=True)

        from langchain_openai import ChatOpenAI
        from langchain_core.tools import tool as lc_tool
        from langchain_core.messages import HumanMessage, SystemMessage
        from langgraph.prebuilt import create_react_agent
        from agent.tools.tavily import tavily_search
        from agent.tools.newsapi import newsapi_search
        from agent.tools.hackernews import hackernews_search
        from agent.tools.ted import ted_search as _ted_search

        today = datetime.utcnow().strftime("%d %B %Y")

        raw_tenders = []
        try:
            raw_tenders = _ted_search(sector=sector, time_range_days=days)
            logger.info(
                f"[{state['run_id']}] collect_opportunities — TED: {len(raw_tenders)} tenders"
            )
        except Exception as e:
            logger.error(f"[{state['run_id']}] collect_opportunities — TED error: {e}")

        @lc_tool
        def search_web(query: str) -> list[dict]:
            """Search the web for business expansion news, press releases,
            budget approvals, city council decisions, and procurement plans."""
            return tavily_search(query, days)

        @lc_tool
        def search_news(query: str) -> list[dict]:
            """Search news articles for business expansion signals and
            public sector procurement announcements."""
            return newsapi_search(query, days)

        @lc_tool
        def search_hackernews(query: str) -> list[dict]:
            """Search Hacker News for technology procurement signals and
            digital transformation project discussions."""
            return hackernews_search(query, days)

        tools = [search_web, search_news, search_hackernews]
        llm   = ChatOpenAI(model="gpt-4o", temperature=0)
        agent = create_react_agent(llm, tools)

        queries = state["search_queries"]

        prompt = f"""You are a business development researcher for PARTTEAM & OEMKIOSKS,
a company that manufactures DOOH digital signage displays and self-service kiosks.

Today's date is {today}. Find business opportunity signals in the {sector} sector
from the last {days} days.

You are looking for TWO types of signals:

TYPE 1 — PRIVATE EXPANSION:
Private sector expansion where PARTTEAM could sell kiosks or digital signage NOW.
Examples:
- "McDonald's announces 50 new restaurants in Portugal"
- "Lidl expanding with 30 new stores in Spain with self-checkout focus"
- "Heathrow Terminal 3 renovation — digital wayfinding upgrade announced"

TYPE 2 — PRE-TENDER PUBLIC SIGNALS:
Public sector budget approvals, investment plans, strategy documents that will
likely result in a public tender in 3-12 months.
Examples:
- "Porto City Council approves €3M smart city budget Q3 2026"
- "NHS announces digital patient check-in modernisation programme"
- "EU Smart Cities initiative — €500M fund open for applications"

Suggested search queries:
{chr(10).join(f'- {q}' for q in queries)}

Instructions:
- Run at least 2 queries with search_web and 2 with search_news
- Focus on SPECIFIC announcements with named organisations, locations, scale
- Generic industry news is NOT an opportunity — skip it
- Run search_hackernews once for digital transformation signals

Return a summary of ALL signals found — both types mixed together is fine."""

        logger.info(f"[{state['run_id']}] collect_opportunities — running ReAct agent")
        agent_response = agent.invoke({"messages": [{"role": "user", "content": prompt}]})

        # FIX 5 — two-layer dedup: URL exact match + title word-overlap
        all_signals  = []
        seen_urls    = set()
        seen_titles  = []
        messages     = agent_response.get("messages", [])

        for message in messages:
            if hasattr(message, "content") and hasattr(message, "name"):
                try:
                    import json as _json
                    content = message.content
                    if isinstance(content, str):
                        parsed = _json.loads(content)
                        if isinstance(parsed, list):
                            for signal in parsed:
                                url   = signal.get("url", "").strip()
                                title = signal.get("title", "").strip()
                                if url and url in seen_urls:
                                    continue
                                if title and _is_duplicate_title(title, seen_titles):
                                    continue
                                if url:
                                    seen_urls.add(url)
                                if title:
                                    seen_titles.append(title)
                                all_signals.append(signal)
                except Exception:
                    pass

        logger.info(
            f"[{state['run_id']}] collect_opportunities — ReAct done — "
            f"{len(all_signals)} signals after dedup"
        )

        raw_private_signals   = []
        raw_pretender_signals = []

        if all_signals:
            signals_for_classification = ""
            for i, s in enumerate(all_signals, 1):
                signals_for_classification += (
                    f"\nSignal {i}:\n"
                    f"  Title:   {s.get('title','')}\n"
                    f"  Snippet: {s.get('snippet','')[:200]}\n"
                    f"  Source:  {s.get('source','')}\n"
                )

            classification_system = """You are classifying business opportunity signals into two types.

PRIVATE_EXPANSION: A private company (retailer, restaurant chain, airport, transport operator)
announcing expansion, renovation, or rollout where they would BUY kiosks or digital signage
directly. The buyer is a private organisation. Action: call the buyer now.

PRETENDER_SIGNAL: A public sector body (city council, government, NHS, EU institution)
announcing a budget approval, investment plan, or strategy that will likely result in a
PUBLIC TENDER for kiosks or digital signage in 3-12 months. Not on TED yet.
Action: monitor and position now.

Return ONLY a JSON array. One object per signal. Fields:
- index: the signal number (integer)
- type: "private_expansion" or "pretender_signal"

Example: [{"index": 1, "type": "private_expansion"}, {"index": 2, "type": "pretender_signal"}]

Return ONLY the JSON array, no markdown, no explanation."""

            classification_user = f"""Classify these {len(all_signals)} signals:
{signals_for_classification}"""

            try:
                clf_llm = ChatOpenAI(model="gpt-4o", temperature=0)
                clf_response = clf_llm.invoke([
                    SystemMessage(content=classification_system),
                    HumanMessage(content=classification_user),
                ])
                content = clf_response.content.strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[1].rsplit("```", 1)[0]
                classifications = json.loads(content)

                idx_to_type = {c["index"]: c["type"] for c in classifications}

                for i, signal in enumerate(all_signals, 1):
                    signal_type = idx_to_type.get(i, "private_expansion")
                    signal["signal_type"] = signal_type
                    if signal_type == "pretender_signal":
                        raw_pretender_signals.append(signal)
                    else:
                        raw_private_signals.append(signal)

                logger.info(
                    f"[{state['run_id']}] collect_opportunities — classification done — "
                    f"private={len(raw_private_signals)} | pretender={len(raw_pretender_signals)}"
                )

            except Exception as e:
                logger.error(
                    f"[{state['run_id']}] collect_opportunities — classification error: {e} — "
                    f"falling back: all {len(all_signals)} signals → private"
                )
                for signal in all_signals:
                    signal["signal_type"] = "private_expansion"
                    raw_private_signals.append(signal)

        logger.info(
            f"[{state['run_id']}] collect_opportunities — OK — "
            f"tenders={len(raw_tenders)} | "
            f"private={len(raw_private_signals)} | "
            f"pretender={len(raw_pretender_signals)}"
        )
        return {
            "raw_tenders":           raw_tenders,
            "raw_private_signals":   raw_private_signals,
            "raw_pretender_signals": raw_pretender_signals,
        }

    except Exception as e:
        msg = f"Unexpected error in collect_opportunities: {e}"
        logger.error(f"[{state['run_id']}] collect_opportunities — UNEXPECTED ERROR — {msg}", exc_info=True)
        return {
            "raw_tenders":           [],
            "raw_private_signals":   [],
            "raw_pretender_signals": [],
            "error":                 msg,
        }


# ---------------------------------------------------------------------------
# Node 8 — evaluate_opportunities  (V1.1 + FIX 1 + FIX 2 + FIX 3 + FIX 4)
# ---------------------------------------------------------------------------

def evaluate_opportunities(state: AgentState) -> dict:
    """
    FIX 1: tender_system returns translated_title; _evaluate_item overwrites title.
    FIX 2: Explicit High/Medium/Low rubric added to all three system prompts.
    FIX 3: "Irrelevant" impact_level — LLM rejects unrelated signals; _evaluate_item drops them.
    FIX 4: Confidence = (llm_score * 0.5) + (rag_score * 0.3) + (source_quality * 0.2).
           relevance_score (1-10) returned by LLM in all evaluation JSON responses.
    """
    try:
        tenders   = state["raw_tenders"][:3]
        privates  = state["raw_private_signals"][:3]
        pretender = state["raw_pretender_signals"][:3]

        logger.info(
            f"[{state['run_id']}] evaluate_opportunities — start — "
            f"tenders={len(tenders)} | private={len(privates)} | pretender={len(pretender)}"
        )

        if not tenders and not privates and not pretender:
            logger.warning(f"[{state['run_id']}] evaluate_opportunities — nothing to evaluate")
            return {
                "evaluated_tenders":   [],
                "evaluated_private":   [],
                "evaluated_pretender": [],
                "llm_calls_made":      state["llm_calls_made"],
            }

        from dotenv import load_dotenv
        load_dotenv(override=True)

        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage, SystemMessage
        from rag.retriever import retrieve_strategic_objectives, retrieve_business_profile

        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        llm_calls_made      = state["llm_calls_made"]
        evaluated_tenders   = []
        evaluated_private   = []
        evaluated_pretender = []
        source_quality_map  = {"primary": 1.0, "secondary": 0.6, "unknown": 0.3}

        def _get_rag_context(sector: str) -> tuple[float, str]:
            try:
                objective_chunks = retrieve_strategic_objectives(
                    query=f"{sector} digital signage kiosk procurement opportunity",
                    top_k=2,
                )
                product_chunks = retrieve_business_profile(
                    query=f"{sector} kiosk signage display hardware software",
                    top_k=2,
                )
                rag_chunks  = objective_chunks + product_chunks
                rag_score   = rag_chunks[0]["score"] if rag_chunks else 0.0
                rag_context = "\n\n".join([
                    f"[{c['chunk_type'].upper()} — {c['heading']}]\n{c['text']}"
                    for c in rag_chunks
                ])
                return rag_score, rag_context
            except Exception as e:
                logger.error(f"[{state['run_id']}] evaluate_opportunities — RAG error: {e}")
                return 0.0, "No strategic context available."

        # ── FIX 1 + FIX 2 + FIX 3 + FIX 4 — tender_system ──────────────
        tender_system = """You are a business development analyst for PARTTEAM & OEMKIOSKS,
a Portuguese manufacturer of DOOH digital signage and self-service kiosks.

Evaluate this EU public tender. Focus on: bid or no-bid decision, product fit,
deadline urgency, and which strategic objective this serves.

Language instruction: input may be in any language. All output must be in English.
If the tender title is not in English, translate it to English for the translated_title field.

Impact classification criteria:
- High: strong product fit + clear path to revenue + aligns with a strategic objective
- Medium: partial fit or uncertain timeline — worth tracking
- Low: weak fit, wrong geography, or outside product scope
- Irrelevant: no realistic connection to digital signage, self-service kiosks, or DOOH

If this tender has no realistic connection to digital signage, self-service kiosks,
or DOOH — set impact_level to "Irrelevant". Only evaluate fit for tenders that could
plausibly involve PARTTEAM products.

Return a JSON object with exactly:
- translated_title: string (tender title in English — translate if needed, keep if already English)
- impact_level: "High" | "Medium" | "Low" | "Irrelevant"
- bid_fit_summary: string (2-3 sentences — fit? which product? why?)
- strategic_link: string (which PARTTEAM objective)
- recommended_action: string (one sentence — what to do)
- deadline_urgency: "Immediate" | "Soon" | "Monitor"
- relevance_score: integer 1-10 (your own assessment of strategic importance to PARTTEAM)

Return ONLY the JSON object, no markdown."""

        # ── FIX 2 + FIX 3 + FIX 4 — private_system ──────────────────────
        private_system = """You are a business development analyst for PARTTEAM & OEMKIOSKS,
a Portuguese manufacturer of DOOH digital signage and self-service kiosks.

Evaluate this private sector expansion signal. This is a commercial opportunity —
a private company is expanding and may need kiosks or digital signage.
Focus on: is this a real sales opportunity? Who is the buyer? What would PARTTEAM sell them?
What is the next commercial action?

Impact classification criteria:
- High: strong product fit + clear path to revenue + aligns with a strategic objective
- Medium: partial fit or uncertain timeline — worth tracking
- Low: weak fit, wrong geography, or outside product scope
- Irrelevant: no realistic connection to digital signage, self-service kiosks, or DOOH

If this signal has no realistic connection to digital signage, self-service kiosks,
or DOOH — set impact_level to "Irrelevant". Only evaluate fit for signals that could
plausibly involve PARTTEAM products.

Return a JSON object with exactly:
- impact_level: "High" | "Medium" | "Low" | "Irrelevant"
- bid_fit_summary: string (2-3 sentences — who is expanding? what would PARTTEAM sell?)
- strategic_link: string (which PARTTEAM objective)
- recommended_action: string (one sentence — commercial action)
- deadline_urgency: "Immediate" | "Soon" | "Monitor"
- relevance_score: integer 1-10 (your own assessment of strategic importance to PARTTEAM)

Return ONLY the JSON object, no markdown."""

        # ── FIX 2 + FIX 3 + FIX 4 — pretender_system ────────────────────
        pretender_system = """You are a business development analyst for PARTTEAM & OEMKIOSKS,
a Portuguese manufacturer of DOOH digital signage and self-service kiosks.

Evaluate this pre-tender public signal. A public authority has approved a budget or
announced an investment plan. A tender will likely appear on TED in 3-12 months.
Focus on: positioning opportunity, which product fits, what PARTTEAM should do NOW
to be ready when the tender drops.

Impact classification criteria:
- High: strong product fit + clear path to revenue + aligns with a strategic objective
- Medium: partial fit or uncertain timeline — worth tracking
- Low: weak fit, wrong geography, or outside product scope
- Irrelevant: no realistic connection to digital signage, self-service kiosks, or DOOH

If this signal has no realistic connection to digital signage, self-service kiosks,
or DOOH — set impact_level to "Irrelevant". Only evaluate fit for signals that could
plausibly involve PARTTEAM products.

Return a JSON object with exactly:
- impact_level: "High" | "Medium" | "Low" | "Irrelevant"
- bid_fit_summary: string (2-3 sentences — what is the authority planning? what would PARTTEAM bid?)
- strategic_link: string (which PARTTEAM objective)
- recommended_action: string (one sentence — positioning action)
- deadline_urgency: "Monitor"
- relevance_score: integer 1-10 (your own assessment of strategic importance to PARTTEAM)

Return ONLY the JSON object, no markdown."""

        def _evaluate_item(item: dict, system_prompt: str, item_type: str) -> dict | None:
            nonlocal llm_calls_made
            if llm_calls_made >= 10:
                logger.warning(
                    f"[{state['run_id']}] evaluate_opportunities — budget reached at {item_type}"
                )
                return None

            rag_score, rag_context = _get_rag_context(state["sector"] or state["subject"])

            title   = item.get("title", "")
            snippet = item.get("snippet", item.get("bid_fit_summary", ""))[:400]

            if item_type == "tender":
                context_block = f"""OPPORTUNITY TYPE: EU Public Tender
TITLE: {title}
CONTRACTING AUTHORITY: {item.get('authority', '')}
COUNTRY: {item.get('country', '')}
ESTIMATED VALUE: {item.get('value', 'Not specified')}
DEADLINE: {item.get('deadline', 'Not specified')}
CPV CODES: {', '.join(str(c) for c in item.get('cpv_codes', []))}
SECTOR: {state['sector']}"""

            elif item_type == "private":
                context_block = f"""OPPORTUNITY TYPE: Private Sector Expansion
TITLE: {title}
SNIPPET: {snippet}
SOURCE: {item.get('source', '')}
PUBLISHED: {item.get('published_at', '')}
SECTOR: {state['sector']}"""

            else:
                context_block = f"""OPPORTUNITY TYPE: Pre-Tender Public Signal
TITLE: {title}
SNIPPET: {snippet}
SOURCE: {item.get('source', '')}
PUBLISHED: {item.get('published_at', '')}
SECTOR: {state['sector']}
NOTE: This is a budget approval or investment plan — no tender exists yet."""

            user_prompt = f"""{context_block}

STRATEGIC CONTEXT FROM KNOWLEDGE BASE:
{rag_context}

Evaluate this opportunity for PARTTEAM & OEMKIOSKS."""

            try:
                response = llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ])
                llm_calls_made += 1
                content = response.content.strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[1].rsplit("```", 1)[0]
                evaluation = json.loads(content)

                # FIX 3 — drop irrelevant signals entirely
                if evaluation.get("impact_level") == "Irrelevant":
                    logger.info(
                        f"[{state['run_id']}] evaluate_opportunities — "
                        f"filtered irrelevant ({item_type}): '{title[:60]}'"
                    )
                    return None

                # FIX 4 — new confidence formula
                llm_score      = evaluation.get("relevance_score", 5) / 10
                source_quality = source_quality_map.get(item.get("source_type", "primary"), 0.6)
                confidence     = round(
                    ((llm_score * 0.5) + (rag_score * 0.3) + (source_quality * 0.2)) * 10, 1
                )

                logger.info(
                    f"[{state['run_id']}] evaluate_opportunities — {item_type}: "
                    f"'{title[:50]}' → {evaluation.get('impact_level')} | "
                    f"llm_score={evaluation.get('relevance_score')} | "
                    f"confidence={confidence}"
                )

                # FIX 1 — use translated_title for tenders
                resolved_title = (
                    evaluation.get("translated_title", title)
                    if item_type == "tender"
                    else title
                )

                return {
                    **item,
                    "title":              resolved_title,
                    "impact_level":       evaluation.get("impact_level", "Low"),
                    "bid_fit_summary":    evaluation.get("bid_fit_summary", ""),
                    "strategic_link":     evaluation.get("strategic_link", ""),
                    "recommended_action": evaluation.get("recommended_action", ""),
                    "deadline_urgency":   evaluation.get("deadline_urgency", "Monitor"),
                    "relevance_score":    evaluation.get("relevance_score", 5),
                    "rag_score":          round(rag_score, 4),
                    "confidence":         confidence,
                }

            except Exception as e:
                logger.error(
                    f"[{state['run_id']}] evaluate_opportunities — LLM error ({item_type}): {e}"
                )
                llm_calls_made += 1
                return {
                    **item,
                    "impact_level":       "Low",
                    "bid_fit_summary":    "Evaluation failed.",
                    "strategic_link":     "Unknown",
                    "recommended_action": "",
                    "deadline_urgency":   "Monitor",
                    "relevance_score":    0,
                    "rag_score":          0.0,
                    "confidence":         0.0,
                }

        for t in tenders:
            result = _evaluate_item(t, tender_system, "tender")
            if result:
                evaluated_tenders.append(result)

        for p in privates:
            result = _evaluate_item(p, private_system, "private")
            if result:
                evaluated_private.append(result)

        for pt in pretender:
            result = _evaluate_item(pt, pretender_system, "pretender")
            if result:
                evaluated_pretender.append(result)

        logger.info(
            f"[{state['run_id']}] evaluate_opportunities — OK — "
            f"tenders={len(evaluated_tenders)} | "
            f"private={len(evaluated_private)} | "
            f"pretender={len(evaluated_pretender)} | "
            f"llm_calls={llm_calls_made}"
        )
        return {
            "evaluated_tenders":   evaluated_tenders,
            "evaluated_private":   evaluated_private,
            "evaluated_pretender": evaluated_pretender,
            "llm_calls_made":      llm_calls_made,
        }

    except Exception as e:
        msg = f"Unexpected error in evaluate_opportunities: {e}"
        logger.error(
            f"[{state['run_id']}] evaluate_opportunities — UNEXPECTED ERROR — {msg}",
            exc_info=True
        )
        return {
            "evaluated_tenders":   [],
            "evaluated_private":   [],
            "evaluated_pretender": [],
            "llm_calls_made":      state["llm_calls_made"],
            "error":               msg,
        }


# ---------------------------------------------------------------------------
# Node 9 — generate_opportunity_brief  (V1.1 — unchanged)
# ---------------------------------------------------------------------------

def generate_opportunity_brief(state: AgentState) -> dict:
    """
    Generates the 1-page Business Opportunities executive snapshot.
    Three sections: Live EU Tenders / Private Opportunities / Pre-Tender Signals.
    One LLM call.
    """
    try:
        sector         = state["sector"] or state["subject"]
        tenders        = state["evaluated_tenders"]
        privates       = state["evaluated_private"]
        pretender      = state["evaluated_pretender"]
        llm_calls_made = state["llm_calls_made"]

        logger.info(
            f"[{state['run_id']}] generate_opportunity_brief — start — "
            f"sector='{sector}' | tenders={len(tenders)} | "
            f"private={len(privates)} | pretender={len(pretender)}"
        )

        from dotenv import load_dotenv
        load_dotenv(override=True)

        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = ChatOpenAI(model="gpt-4o", temperature=0)

        if not tenders and not privates and not pretender:
            brief = (
                f"Business Opportunities Snapshot — {sector} "
                f"(Last {state['time_range_days']} Days)\n\n"
                f"No opportunities found in this sector for the selected time window.\n\n"
                f"── EXECUTIVE TAKEAWAY ─────────────────────────────────\n"
                f"No actionable opportunities identified. Consider expanding the time window "
                f"or reviewing sector keyword coverage."
            )
            return {"final_brief": brief, "llm_calls_made": llm_calls_made}

        impact_order = {"High": 0, "Medium": 1, "Low": 2}

        def _build_block(items, fields):
            if not items:
                return None
            sorted_items = sorted(items, key=lambda x: impact_order.get(x.get("impact_level", "Low"), 2))
            block = ""
            for item in sorted_items:
                block += "---\n"
                for label, key in fields:
                    val = item.get(key, "")
                    if isinstance(val, list):
                        val = ", ".join(str(v) for v in val)
                    if val:
                        block += f"{label}: {val}\n"
                block += "\n"
            return block

        tenders_block = _build_block(tenders, [
            ("Title",              "title"),
            ("Authority",          "authority"),
            ("Country",            "country"),
            ("Value",              "value"),
            ("Deadline",           "deadline"),
            ("Impact",             "impact_level"),
            ("Urgency",            "deadline_urgency"),
            ("Confidence",         "confidence"),
            ("Fit Summary",        "bid_fit_summary"),
            ("Strategic Link",     "strategic_link"),
            ("Recommended Action", "recommended_action"),
            ("Source",             "url"),
        ]) or "No live EU tenders found for this sector in the selected time window."

        private_block = _build_block(privates, [
            ("Title",              "title"),
            ("Source",             "source"),
            ("Published",          "published_at"),
            ("Impact",             "impact_level"),
            ("Urgency",            "deadline_urgency"),
            ("Confidence",         "confidence"),
            ("Fit Summary",        "bid_fit_summary"),
            ("Strategic Link",     "strategic_link"),
            ("Recommended Action", "recommended_action"),
            ("Source URL",         "url"),
        ]) or "No private expansion signals found for this sector in the selected time window."

        pretender_block = _build_block(pretender, [
            ("Title",              "title"),
            ("Source",             "source"),
            ("Published",          "published_at"),
            ("Impact",             "impact_level"),
            ("Confidence",         "confidence"),
            ("Fit Summary",        "bid_fit_summary"),
            ("Strategic Link",     "strategic_link"),
            ("Recommended Action", "recommended_action"),
            ("Source URL",         "url"),
        ]) or "No pre-tender public signals found for this sector in the selected time window."

        system_prompt = """You are a business development analyst writing a 1-page opportunity
brief for PARTTEAM & OEMKIOSKS leadership.

Format EXACTLY as follows:

Business Opportunities Snapshot — {SECTOR} (Last {N} Days)

── LIVE EU TENDERS ──────────────────────────────────
[For each tender:
  • [TITLE] — [COUNTRY] | Deadline: [DATE] | Value: [VALUE] | Urgency: [URGENCY]
    Fit: [bid_fit_summary, 1 sentence]
    Action: [recommended_action]
    Link: [url]
]
If none: "No live EU tenders in this sector this period."

── PRIVATE OPPORTUNITIES ────────────────────────────
[For each private signal:
  • [TITLE] | [SOURCE] | [DATE]
    Fit: [bid_fit_summary, 1 sentence]
    Action: [recommended_action]
    Link: [url]
]
If none: "No private expansion signals in this sector this period."

── PRE-TENDER SIGNALS ───────────────────────────────
[For each pre-tender signal:
  • [TITLE] | [SOURCE] | [DATE]
    Signal: [what the authority approved or announced]
    Action: [recommended_action — positioning, not immediate bid]
    Link: [url]
]
If none: "No pre-tender public signals in this sector this period."

── EXECUTIVE TAKEAWAY ───────────────────────────────
[3-4 sentences. What is the biggest opportunity this week?
What should leadership prioritise across all three signal types?
Be specific and actionable.]

Return ONLY the formatted brief, no other text."""

        user_prompt = f"""Generate the opportunity brief for:

Sector:      {sector}
Time Window: Last {state['time_range_days']} days

LIVE EU TENDERS:
{tenders_block}

PRIVATE OPPORTUNITIES:
{private_block}

PRE-TENDER SIGNALS:
{pretender_block}"""

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])
        llm_calls_made += 1

        logger.info(
            f"[{state['run_id']}] generate_opportunity_brief — OK — "
            f"llm_calls={llm_calls_made}"
        )
        return {
            "final_brief":    response.content.strip(),
            "llm_calls_made": llm_calls_made,
            "error":          None,
        }

    except Exception as e:
        msg = f"Unexpected error in generate_opportunity_brief: {e}"
        logger.error(
            f"[{state['run_id']}] generate_opportunity_brief — UNEXPECTED ERROR — {msg}",
            exc_info=True
        )
        fallback = (
            f"Business Opportunities Snapshot — {state.get('sector', state['subject'])} "
            f"(Last {state['time_range_days']} Days)\n\n"
            f"Brief generation failed: {msg}\nRun ID: {state['run_id']}"
        )
        return {"final_brief": fallback, "llm_calls_made": state["llm_calls_made"], "error": msg}
