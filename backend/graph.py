"""
LangGraph Orchestration
Builds and compiles the 3-agent pipeline:
  diagnose → plan → critique → [pass: END | fail: plan]
"""

from __future__ import annotations

from langgraph.graph import StateGraph, END

from backend.state import GapGraphState
from backend.agents.diagnoser import diagnose
from backend.agents.planner import plan
from backend.agents.critic import critique, route_critique


def _increment_retry(state: GapGraphState) -> GapGraphState:
    """Used when routing back to plan after a failed critique."""
    return {**state, "retry_count": state.get("retry_count", 0) + 1}


def build_graph():
    """Compile and return the GapGraph LangGraph pipeline."""
    g = StateGraph(GapGraphState)

    # Register agent nodes
    g.add_node("diagnose", diagnose)
    g.add_node("plan", plan)
    g.add_node("critique", critique)
    g.add_node("increment_retry", _increment_retry)

    # Entry point
    g.set_entry_point("diagnose")

    # Fixed edges
    g.add_edge("diagnose", "plan")
    g.add_edge("plan", "critique")

    # Conditional edge from critique
    g.add_conditional_edges(
        "critique",
        route_critique,
        {
            "pass": END,
            "fail": "increment_retry",
        },
    )
    g.add_edge("increment_retry", "plan")

    return g.compile()


# Singleton compiled graph
_compiled_graph = None


def get_graph():
    """Return the singleton compiled graph (lazy initialization)."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph
