"""
LangGraph Workflow — Builds and compiles the multi-agent StateGraph.
"""
import logging
from langgraph.graph import StateGraph, END

from src.workflows.state import AgentState
from src.workflows.nodes import (
    orchestrate_node,
    research_node,
    analyze_node,
    write_node,
    finalize_node,
)

logger = logging.getLogger(__name__)


def build_graph():
    """
    Build and compile the IntelliAgents StateGraph.

    Graph structure:
        orchestrate → research → analyze → write → finalize → END
    """
    graph = StateGraph(AgentState)

    # ── Register nodes ──
    graph.add_node("orchestrate", orchestrate_node)
    graph.add_node("research", research_node)
    graph.add_node("analyze", analyze_node)
    graph.add_node("write", write_node)
    graph.add_node("finalize", finalize_node)

    # ── Set entry point ──
    graph.set_entry_point("orchestrate")

    # ── Linear edges ──
    graph.add_edge("orchestrate", "research")
    graph.add_edge("research", "analyze")
    graph.add_edge("analyze", "write")
    graph.add_edge("write", "finalize")

    # ── Terminal edge ──
    graph.add_edge("finalize", END)

    compiled = graph.compile()
    logger.info("IntelliAgents StateGraph compiled successfully.")
    return compiled


# Module-level compiled graph (import and use this)
intelliagents_graph = build_graph()
