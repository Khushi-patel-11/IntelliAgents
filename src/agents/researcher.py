"""
Researcher Agent — Gathers information using web search and document loading.
"""
from typing import Any, Dict

from langchain.messages import HumanMessage, SystemMessage

from src.agents.base_agent import BaseAgent
from src.tools.search import web_search, format_results_as_text
from src.workflows.state import AgentState

SYSTEM_PROMPT = """You are a Research Agent specializing in information gathering and synthesis.

You will receive a research task and raw web search results. Your job is to:
1. Analyze the search results critically
2. Extract the most relevant and accurate information
3. Organize findings into clear, structured sections
4. Note any data gaps or contradictions
5. Always cite sources with their URLs

Format your output as:
## Key Findings
[numbered list of key facts/data points]

## Detailed Research
[organized by sub-topic, with citations]

## Data Sources
[list of sources used]

## Research Gaps
[what information was unavailable or unclear]

Be factual, objective, and thorough. Do not make up information.
"""


class ResearcherAgent(BaseAgent):
    """Performs web research and synthesizes findings."""

    def __init__(self):
        super().__init__(name="Researcher", temperature=0.1)

    def run(self, state: AgentState) -> Dict[str, Any]:
        task = state["task"]
        subtasks = state.get("subtasks", [])

        # Find the research subtask description
        research_desc = next(
            (s["description"] for s in subtasks if s.get("agent") == "researcher"),
            task,
        )

        state = self.log_entry(state, "Starting web research phase.")

        # Generate search queries from the task
        queries = self._generate_queries(task)
        all_results_text = []

        for i, query in enumerate(queries, 1):
            state = self.log_entry(state, f"Starting web search [{i}/{len(queries)}]: \"{query}\"")
            results = web_search(query, num_results=4)
            state = self.log_entry(state, f"Found {len(results)} results. Fetching top documents.")
            all_results_text.append(f"### Search Query: {query}\n{format_results_as_text(results)}")

        combined_results = "\n\n".join(all_results_text)

        state = self.log_entry(state, "Processing search results and extracting insights.")

        # Ask LLM to synthesize the raw results
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Research Task: {research_desc}\n\nRaw Search Results:\n{combined_results}"),
        ]
        response = self.llm.invoke(messages)
        research_data = self._extract_text(response)

        state = self.log_entry(state, "Research complete. Handing off to Analyst agent.")

        return {
            **state,
            "research_data": research_data,
            "current_step": "analyze",
        }

    def _generate_queries(self, task: str) -> list:
        """Generate 2-3 targeted search queries for the task."""
        messages = [
            SystemMessage(content="Generate 2-3 specific web search queries for researching the given task. Respond with ONLY a JSON array of strings. Example: [\"query 1\", \"query 2\"]"),
            HumanMessage(content=f"Task: {task}"),
        ]
        response = self.llm.invoke(messages)
        raw = self._extract_text(response)

        import json, re
        cleaned = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
        try:
            queries = json.loads(cleaned)
            if isinstance(queries, list) and queries:
                return queries[:3]
        except Exception:
            pass
        # Fallback: use the task itself as a single query
        return [task]
