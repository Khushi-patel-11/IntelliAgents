"""
Analyst Agent — Processes research data to identify patterns, trends, and insights.
"""
from typing import Any, Dict

from langchain.messages import HumanMessage, SystemMessage

from src.agents.base_agent import BaseAgent
from src.workflows.state import AgentState

SYSTEM_PROMPT = """You are an Analyst Agent specializing in data analysis, pattern recognition, and insight generation.

You will receive research findings and must:
1. Identify key trends and patterns in the data
2. Perform comparative analysis where applicable
3. Highlight significant statistics and metrics
4. Generate actionable insights from the findings
5. Assess confidence levels in different conclusions
6. Spot contradictions or anomalies in the data

Format your analysis as:
## Executive Insights
[3-5 bullet points of the most important findings]

## Trend Analysis
[identified patterns and their significance]

## Comparative Analysis
[if applicable, comparisons between entities/options]

## Key Metrics & Statistics
[quantitative data points highlighted]

## Risk Factors & Uncertainties
[limitations, contradictions, or cautionary notes]

## Strategic Recommendations
[actionable next steps or conclusions based on analysis]

Be analytical, precise, and evidence-based. Clearly distinguish between facts and interpretations.
"""


class AnalystAgent(BaseAgent):
    """Analyzes research data and generates structured insights."""

    def __init__(self):
        super().__init__(name="Analyst", temperature=0.2)

    def run(self, state: AgentState) -> Dict[str, Any]:
        task = state["task"]
        research_data = state.get("research_data", "")
        subtasks = state.get("subtasks", [])

        analysis_desc = next(
            (s["description"] for s in subtasks if s.get("agent") == "analyst"),
            "Analyze the research data and provide strategic insights.",
        )

        state = self.log_entry(state, "Received research data. Beginning analysis phase.")
        state = self.log_entry(state, "Processing dataset and identifying key patterns.")

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=f"Original Task: {task}\n\nAnalysis Goal: {analysis_desc}\n\nResearch Data:\n{research_data}"
            ),
        ]

        response = self.llm.invoke(messages)
        analysis = self._extract_text(response)

        state = self.log_entry(state, "Pattern analysis complete. Identified key trends and insights.")
        state = self.log_entry(state, "Handing off to Writer agent for report synthesis.")

        return {
            **state,
            "analysis": analysis,
            "current_step": "write",
        }
