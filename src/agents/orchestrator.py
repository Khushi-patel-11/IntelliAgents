"""
Orchestrator Agent — Decomposes complex user tasks into a DAG of subtasks
and determines execution order for the specialist agents.
"""
import json
import re
from datetime import datetime
from typing import Any, Dict

from langchain.messages import HumanMessage, SystemMessage

from src.agents.base_agent import BaseAgent
from src.workflows.state import AgentState

SYSTEM_PROMPT = """You are an Orchestrator AI agent responsible for breaking down complex user tasks into structured subtasks.

Given a user task, analyze it and decompose it into 3-5 atomic subtasks that can be assigned to specialist agents:
- researcher: gathers information and facts from web research
- analyst: processes data, identifies patterns and insights
- writer: synthesizes information into a well-structured report

Respond ONLY with valid JSON in this exact format:
{
  "subtasks": [
    {
      "name": "short_task_name",
      "agent": "researcher|analyst|writer",
      "description": "Detailed description of what this subtask should accomplish",
      "dependencies": []
    }
  ],
  "execution_plan": "Brief description of how these tasks relate and should be executed"
}

Rules:
- researcher tasks must come before analyst tasks
- analyst tasks must come before writer tasks
- Keep each subtask focused and specific
- Always include at least one researcher, one analyst, and one writer subtask
"""


class OrchestratorAgent(BaseAgent):
    """Decomposes the user task and plans the workflow."""

    def __init__(self):
        super().__init__(name="Orchestrator", temperature=0.2)

    def run(self, state: AgentState) -> Dict[str, Any]:
        task = state["task"]
        state = self.log_entry(state, f"Task received. Decomposing: \"{task[:60]}...\"" if len(task) > 60 else f"Task received: \"{task}\"")
        state = self.log_entry(state, "Generating subtask plan...")

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"User Task: {task}"),
        ]

        response = self.llm.invoke(messages)
        raw = self._extract_text(response)

        # Parse JSON from response (handle markdown code blocks)
        subtasks = self._parse_subtasks(raw)

        state = self.log_entry(state, f"Decomposed into {len(subtasks)} subtasks.")
        state = self.log_entry(state, "Assigning research subtask to Researcher agent.")

        return {
            **state,
            "subtasks": subtasks,
            "current_step": "research",
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "iteration": 0,
        }

    def _parse_subtasks(self, raw: str) -> list:
        """Extract and parse JSON subtasks from LLM response."""
        # Strip markdown code fences if present
        cleaned = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
        try:
            data = json.loads(cleaned)
            return data.get("subtasks", [])
        except json.JSONDecodeError:
            # Fallback: return a default 3-step plan
            return [
                {"name": "research", "agent": "researcher", "description": "Research the given topic comprehensively.", "dependencies": []},
                {"name": "analyze", "agent": "analyst", "description": "Analyze the research data and extract key insights.", "dependencies": ["research"]},
                {"name": "write", "agent": "writer", "description": "Write a comprehensive report based on analysis.", "dependencies": ["analyze"]},
            ]
