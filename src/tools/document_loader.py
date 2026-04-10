"""
Document Loader Tool — Load content from URLs, PDFs, and text files.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def load_url(url: str, max_chars: int = 5000) -> str:
    """Fetch and extract plain text from a web URL."""
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {"User-Agent": "Mozilla/5.0 (IntelliAgents research bot)"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script/style tags
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        # Clean up excess whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean = "\n".join(lines)
        return clean[:max_chars]
    except Exception as e:
        logger.warning(f"[DocumentLoader] Failed to load URL {url}: {e}")
        return f"[Failed to load {url}: {e}]"


def load_pdf(path: str, max_chars: int = 10000) -> str:
    """Extract text from a PDF file."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(path)
        pages_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text.strip())
        full_text = "\n\n".join(pages_text)
        return full_text[:max_chars]
    except ImportError:
        return "[PDF loading requires pypdf: pip install pypdf]"
    except Exception as e:
        logger.error(f"[DocumentLoader] PDF load failed for {path}: {e}")
        return f"[Failed to load PDF {path}: {e}]"


def load_text(path: str, max_chars: int = 10000) -> str:
    """Load plain text or code file."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(max_chars)
        return content
    except Exception as e:
        logger.error(f"[DocumentLoader] Text load failed for {path}: {e}")
        return f"[Failed to load {path}: {e}]"


def load_document(source: str) -> str:
    """
    Auto-detect source type (URL, PDF, text file) and load accordingly.
    """
    if source.startswith("http://") or source.startswith("https://"):
        return load_url(source)
    if source.lower().endswith(".pdf"):
        return load_pdf(source)
    return load_text(source)
