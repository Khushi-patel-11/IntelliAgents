"""
Web Search Tool — DuckDuckGo-based search with optional Tavily fallback.
"""
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def web_search(query: str, num_results: int = 5) -> List[Dict[str, str]]:
    """
    Search the web for a query and return structured results.

    Returns:
        List of dicts with keys: title, url, snippet
    """
    from config.settings import USE_TAVILY, TAVILY_API_KEY

    if USE_TAVILY:
        return _tavily_search(query, num_results, TAVILY_API_KEY)
    return _duckduckgo_search(query, num_results)


def _duckduckgo_search(query: str, num_results: int = 5) -> List[Dict[str, str]]:
    """Search using DuckDuckGo (no API key required)."""
    try:
        from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=num_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
        logger.info(f"[DuckDuckGo] Found {len(results)} results for: {query}")
        return results
    except Exception as e:
        logger.error(f"[DuckDuckGo] Search failed: {e}")
        return [{"title": "Search unavailable", "url": "", "snippet": str(e)}]


def _tavily_search(query: str, num_results: int, api_key: str) -> List[Dict[str, str]]:
    """Search using Tavily API."""
    try:
        from langchain_community.tools.tavily_search import TavilySearchResults
        import os
        os.environ["TAVILY_API_KEY"] = api_key
        tool = TavilySearchResults(max_results=num_results)
        raw = tool.invoke(query)
        return [
            {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("content", "")}
            for r in raw
        ]
    except Exception as e:
        logger.warning(f"[Tavily] Failed, falling back to DuckDuckGo: {e}")
        return _duckduckgo_search(query, num_results)


def format_results_as_text(results: List[Dict[str, str]]) -> str:
    """Format search results into a readable text block for LLM consumption."""
    if not results:
        return "No search results found."
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r['title']}")
        lines.append(f"    URL: {r['url']}")
        lines.append(f"    {r['snippet']}")
        lines.append("")
    return "\n".join(lines)
