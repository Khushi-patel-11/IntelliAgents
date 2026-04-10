"""
LangGraph Workflow Nodes — Thin wrappers that call each agent's run() method.
"""
from datetime import datetime
from typing import Any, Dict

from src.agents.orchestrator import OrchestratorAgent
from src.agents.researcher import ResearcherAgent
from src.agents.analyst import AnalystAgent
from src.agents.writer import WriterAgent
from src.workflows.state import AgentState

# Instantiate agents once (singleton pattern for the lifetime of the app)
_orchestrator = OrchestratorAgent()
_researcher = ResearcherAgent()
_analyst = AnalystAgent()
_writer = WriterAgent()


def orchestrate_node(state: AgentState) -> Dict[str, Any]:
    """Node: Orchestrator — decomposes the task."""
    return _orchestrator.run(state)


def research_node(state: AgentState) -> Dict[str, Any]:
    """Node: Researcher — gathers information."""
    return _researcher.run(state)


def analyze_node(state: AgentState) -> Dict[str, Any]:
    """Node: Analyst — processes data and generates insights."""
    return _analyst.run(state)


def write_node(state: AgentState) -> Dict[str, Any]:
    """Node: Writer — synthesizes the final report."""
    return _writer.run(state)




def finalize_node(state: AgentState) -> Dict[str, Any]:
    """Node: Finalization — marks the task complete."""
    return {
        **state,
        "status": "completed",
        "completed_at": datetime.now().isoformat(),
        "current_step": "done",
    }


