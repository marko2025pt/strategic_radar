"""
agent/graph.py

LangGraph workflow definition for the Strategic Radar agent.

This module defines the graph structure — nodes, edges, and routing.
It does not contain any node logic. All node implementations live in
nodes.py. This file is purely structural.

Graph structure (V1.0 — Competitor Moves):

    START
      → validate
          → [invalid] → END
          → [valid]   → build_queries
                          → collect_signals
                              → select_signals
                                  → evaluate_signals
                                      → generate_brief
                                          → END

One conditional edge (after validate).
Everything else is a direct edge — no branching, no loops in the graph.
The ReAct loop lives inside the collect_signals node, not in the graph.

V1.1 and V1.2 will add branches after validate by extending
the conditional routing function — nothing else changes.
"""

from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent import nodes


# ---------------------------------------------------------------------------
# Routing function — the one conditional edge
# ---------------------------------------------------------------------------

def route_after_validation(state: AgentState) -> str:
    """
    Called after the validate node.
    Returns the name of the next node to execute.

    V1.0: routes to build_queries or END.
    V1.1/V1.2: will add routing by intelligence_type here.
    """
    if not state["validated"]:
        return END

    # V1.1 extension point:
    # if state["intelligence_type"] == "Business Opportunities":
    #     return "collect_tenders"

    # V1.2 extension point:
    # if state["intelligence_type"] == "Technology Developments":
    #     return "collect_tech_signals"

    return "build_queries"


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    """
    Constructs and compiles the LangGraph workflow.
    Returns a compiled graph ready to invoke with an AgentState.
    Raises RuntimeError if graph construction fails.

    Usage:
        graph = build_graph()
        result = graph.invoke(initial_state)
    """
    try:
        workflow = StateGraph(AgentState)

        # ------------------------------------------------------------------
        # Register nodes
        # Each node is a function from nodes.py that takes AgentState
        # and returns a dict of fields to update in state.
        # ------------------------------------------------------------------

        workflow.add_node("validate",         nodes.validate)
        workflow.add_node("build_queries",    nodes.build_queries)
        workflow.add_node("collect_signals",  nodes.collect_signals)
        workflow.add_node("select_signals",   nodes.select_signals)
        workflow.add_node("evaluate_signals", nodes.evaluate_signals)
        workflow.add_node("generate_brief",   nodes.generate_brief)

        # ------------------------------------------------------------------
        # Entry point
        # ------------------------------------------------------------------

        workflow.set_entry_point("validate")

        # ------------------------------------------------------------------
        # Edges
        # ------------------------------------------------------------------

        # Conditional edge after validation
        workflow.add_conditional_edges(
            "validate",
            route_after_validation,
            {
                "build_queries": "build_queries",
                END: END,
            }
        )

        # Direct edges — linear from here
        workflow.add_edge("build_queries",    "collect_signals")
        workflow.add_edge("collect_signals",  "select_signals")
        workflow.add_edge("select_signals",   "evaluate_signals")
        workflow.add_edge("evaluate_signals", "generate_brief")
        workflow.add_edge("generate_brief",   END)

        return workflow.compile()

    except Exception as e:
        raise RuntimeError(f"Failed to build agent graph: {e}") from e


# ---------------------------------------------------------------------------
# Module-level compiled graph instance
# ---------------------------------------------------------------------------

# Import this in main.py and for testing:
#   from agent.graph import graph
#   result = graph.invoke(state)

graph = build_graph()