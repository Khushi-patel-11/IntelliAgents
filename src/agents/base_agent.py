"""
Base Agent — Abstract base class for all IntelliAgents agents.
"""
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict

from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from config.settings import GOOGLE_API_KEY, GEMINI_MODEL, GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class providing shared LLM, logging, and state utilities."""

    def __init__(self, name: str, temperature: float = 0.3, provider: str = "groq"):
        self.name = name
        self.temperature = temperature
        self.provider = provider.lower()

        if self.provider == "groq":
            self.llm = ChatGroq(
                model=GROQ_MODEL,
                groq_api_key=GROQ_API_KEY,
                temperature=temperature,
                max_retries=6,
            )
            model_name = GROQ_MODEL
        else:
            self.llm = ChatGoogleGenerativeAI(
                model=GEMINI_MODEL,
                google_api_key=GOOGLE_API_KEY,
                temperature=temperature,
                max_retries=6,
            )
            model_name = GEMINI_MODEL
            
        logger.info(f"[{self.name}] Initialized with provider={self.provider}, model={model_name}")

    @retry(
        wait=wait_exponential(multiplier=2, min=4, max=60),
        stop=stop_after_attempt(7)
    )
    def invoke_with_retry(self, messages: list) -> Any:
        """Call the LLM with exponential backoff on rate limits."""
        res = self.llm.invoke(messages)
        
        # Throttling to bypass strict Gemini Free Tier max 15 requests/minute
        if self.provider == "google":
            import time
            time.sleep(4)
        else:
            # Small delay for Groq to avoid hitting RPM/TPM limits too aggressively
            import time
            time.sleep(1)
            
        return res


    @abstractmethod
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's logic and return updated state."""
        pass

    def log_entry(self, state: Dict[str, Any], message: str) -> Dict[str, Any]:
        """Append a timestamped log entry to state['logs'] and display a command panel."""
        entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "agent": self.name,
            "agent_short": self.name[:4].upper(),
            "message": message,
        }
        logs = state.get("logs", [])
        logs.append(entry)
        
        # Command Panel Console Output (Colored)
        print(f"\n\033[96m╔════════════ COMMAND PANEL ════════════╗\033[0m")
        print(f"\033[96m║\033[0m \033[93mAGENT :\033[0m {self.name.upper():<29} \033[96m║\033[0m")
        # Handle wrap for message
        msg_words = message.split()
        lines = []
        curr = ""
        for w in msg_words:
            if len(curr) + len(w) > 28:
                lines.append(curr.strip())
                curr = w + " "
            else:
                curr += w + " "
        if curr: lines.append(curr.strip())
        
        for i, line in enumerate(lines):
            prefix = "ACTION :" if i == 0 else "        "
            print(f"\033[96m║\033[0m \033[92m{prefix}\033[0m {line:<29} \033[96m║\033[0m")
        print(f"\033[96m╚═══════════════════════════════════════╝\033[0m\n")
        
        logger.info(f"[{self.name}] {message}")
        return {**state, "logs": logs}

    def _extract_text(self, response: Any) -> str:
        """Safely extract text content from LLM response."""
        if hasattr(response, "content"):
            content = response.content
            if isinstance(content, list):
                # Handle Gemini thinking model responses
                parts = [
                    p.get("text", "") if isinstance(p, dict) else str(p)
                    for p in content
                ]
                return "\n".join(p for p in parts if p).strip()
            return str(content).strip()
        return str(response).strip()
