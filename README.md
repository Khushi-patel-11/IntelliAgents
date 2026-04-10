# IntelliAgents

IntelliAgents is a small multi-agent orchestration framework that composes specialized agents (orchestrator, researcher, analyst, writer, etc.) to solve complex, multi-step tasks. It includes a FastAPI backend, a Streamlit dashboard, and lightweight shared memory for coordinating workflows.

## Quick Start

Requirements:
- Python 3.10+

Setup (Windows):
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Configure environment variables (if applicable): copy `.env.example` to `.env` and update keys.

Run the services using the launcher script:

- Start backend: `python run.py --api`
- Start UI: `python run.py --ui`
- Start both: `python run.py --both`

The backend runs on `http://localhost:8000` and the Streamlit UI on `http://localhost:8501` by default.

## What’s in this repo

- `src/agents/` — agent implementations and orchestration logic
- `src/workflows/` — LangGraph state and node definitions
- `src/tools/` — helpers: search, document loaders, data analysis
- `src/memory/` — shared memory helpers (SQLite)
- `src/api/` — FastAPI app and routes
- `src/ui/` — Streamlit dashboard
- `config/` — configuration and settings
- `run.py` — convenient launcher for API/UI

## Development

- Run the launcher locally while the virtualenv is active.
- Edit code under `src/` and the FastAPI server will reload automatically when using `--api` (uvicorn `--reload`).

If you'd like, I can also add a short example showing how to submit a task to the API, or include a `.env.example` file if one is missing.

---
Updated README to include concise setup and run instructions.
