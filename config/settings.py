"""
IntelliAgents Configuration Settings
Loads environment variables and provides typed config values.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# ---- LLM Configuration ----
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# ---- Groq Configuration ----
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# ---- Search Configuration ----
TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
USE_TAVILY: bool = bool(TAVILY_API_KEY)

# ---- Persistence ----
SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "./intelliagents.db")

# ---- API Settings ----
API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
API_PORT: int = int(os.getenv("API_PORT", "8000"))

# ---- Agent Settings ----
MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "2"))
MIN_QUALITY_SCORE: int = int(os.getenv("MIN_QUALITY_SCORE", "7"))

# ---- Validation ----
def validate_config() -> None:
    """Raise an error if required configuration is missing."""
    if not GROQ_API_KEY and not GOOGLE_API_KEY:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. Please add it to your .env file. "
            "(Alternatively, GOOGLE_API_KEY can be used if provider is switched back to google)."
        )
