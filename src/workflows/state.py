"""
Shared state schema for the IntelliAgents LangGraph workflow.
"""
from typing import Any, Dict, List, Optional, TypedDict


class SubTask(TypedDict):
    name: str
    agent: str        # orchestrator | researcher | analyst | writer
    description: str
    dependencies: List[str]


class LogEntry(TypedDict):
    timestamp: str
    agent: str
    agent_short: str
    message: str


class AgentState(TypedDict):
    # Core task
    task: str
    task_id: str

    # Orchestrator plan
    subtasks: List[SubTask]
    current_step: str            # which node is active

    # Agent outputs
    research_data: str
    analysis: str
    report: str

    # Execution tracking
    logs: List[LogEntry]
    status: str                  # pending | running | completed | failed
    error: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
