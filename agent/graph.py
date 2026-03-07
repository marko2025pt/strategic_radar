# Version 1.1 — Final demo delivery to Ironhack 2026-03-06
"""
agent/graph.py  —  V1.1

Changes from V1.0:
  - route_after_validation() now routes "Business Opportunities"
    to the collect_opportunities node (V1.1 branch)
  - Three new nodes registered: collect_opportunities,
    evaluate_opportunities, generate_opportunity_brief
  - Two new edge chains added for the V1.1 branch

V1.0 branch is completely unchanged.

Graph structure:

    START
      → validate
          → [invalid]                → END
          → [Competitor Moves]       → build_queries → collect_signals
                                       → select_signals → evaluate_signals
                                       → generate_brief → END
          → [Business Opportunities] → build_queries → collect_opportunities
                                       → evaluate_opportunities
                                       → generate_opportunity_brief → END
"""

from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent import nodes


# ---------------------------------------------------------------------------
# Routing function
# ---------------------------------------------------------------------------

def route_after_validation(state: AgentState) -> str:
    if not state["validated"]:
        return END

    if state["intelligence_type"] == "Business Opportunities":
        return "build_queries_opportunities"

    # V1.2 extension point:
    # if state["intelligence_type"] == "Technology Developments":
    #     return "build_queries_technology"

    return "build_queries"


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    """
    Constructs and compiles the LangGraph workflow.
    Raises RuntimeError if graph construction fails.
    """
    try:
        workflow = StateGraph(AgentState)

        # ------------------------------------------------------------------
        # V1.0 nodes — Competitor Moves
        # ------------------------------------------------------------------
        workflow.add_node("validate",          nodes.validate)
        workflow.add_node("build_queries",     nodes.build_queries)
        workflow.add_node("collect_signals",   nodes.collect_signals)
        workflow.add_node("select_signals",    nodes.select_signals)
        workflow.add_node("evaluate_signals",  nodes.evaluate_signals)
        workflow.add_node("generate_brief",    nodes.generate_brief)

        # ------------------------------------------------------------------
        # V1.1 nodes — Business Opportunities
        # ------------------------------------------------------------------
        workflow.add_node("build_queries_opportunities",    nodes.build_queries)
        workflow.add_node("collect_opportunities",          nodes.collect_opportunities)
        workflow.add_node("evaluate_opportunities",         nodes.evaluate_opportunities)
        workflow.add_node("generate_opportunity_brief",     nodes.generate_opportunity_brief)

        # ------------------------------------------------------------------
        # Entry point
        # ------------------------------------------------------------------
        workflow.set_entry_point("validate")

        # ------------------------------------------------------------------
        # Conditional edge after validate
        # ------------------------------------------------------------------
        workflow.add_conditional_edges(
            "validate",
            route_after_validation,
            {
                "build_queries":               "build_queries",
                "build_queries_opportunities": "build_queries_opportunities",
                END:                            END,
            }
        )

        # ------------------------------------------------------------------
        # V1.0 edges — linear
        # ------------------------------------------------------------------
        workflow.add_edge("build_queries",    "collect_signals")
        workflow.add_edge("collect_signals",  "select_signals")
        workflow.add_edge("select_signals",   "evaluate_signals")
        workflow.add_edge("evaluate_signals", "generate_brief")
        workflow.add_edge("generate_brief",   END)

        # ------------------------------------------------------------------
        # V1.1 edges — linear
        # ------------------------------------------------------------------
        workflow.add_edge("build_queries_opportunities", "collect_opportunities")
        workflow.add_edge("collect_opportunities",       "evaluate_opportunities")
        workflow.add_edge("evaluate_opportunities",      "generate_opportunity_brief")
        workflow.add_edge("generate_opportunity_brief",  END)

        return workflow.compile()

    except Exception as e:
        raise RuntimeError(f"Failed to build agent graph: {e}") from e


graph = build_graph()