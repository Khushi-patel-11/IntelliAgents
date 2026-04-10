"""
FastAPI Backend — REST API for task submission, status, and log streaming.
"""
import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from config.settings import validate_config
from src.memory.shared_memory import memory
from src.workflows.graph import intelliagents_graph

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("intelliagents.api")

# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="IntelliAgents API",
    description="Multi-Agent AI System — REST API for task orchestration",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory task registry for running tasks
_running_tasks: Dict[str, asyncio.Task] = {}


# ── Request / Response Models ─────────────────────────────────────────────────
class TaskRequest(BaseModel):
    task: str

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

class TaskStatus(BaseModel):
    task_id: str
    task: str
    status: str
    current_step: Optional[str] = None
    report: Optional[str] = None
    logs: Optional[List[Dict[str, Any]]] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


# ── Background Worker ─────────────────────────────────────────────────────────
async def _run_workflow(task_id: str, task: str) -> None:
    """Run the LangGraph workflow in a background thread."""
    initial_state = {
        "task": task,
        "task_id": task_id,
        "subtasks": [],
        "current_step": "orchestrate",
        "research_data": "",
        "analysis": "",
        "report": "",
        "logs": [],
        "status": "running",
        "error": None,
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
    }

    try:
        loop = asyncio.get_event_loop()
        # Run the synchronous LangGraph workflow in a thread pool
        final_state = await loop.run_in_executor(
            None,
            lambda: intelliagents_graph.invoke(initial_state),
        )
        memory.update_state(task_id, final_state)
        logger.info(f"Task {task_id} completed with status: {final_state.get('status')}")
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}", exc_info=True)
        error_state = {**initial_state, "status": "failed", "error": str(e)}
        memory.update_state(task_id, error_state)


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    try:
        validate_config()
        logger.info("IntelliAgents API started. Config validated.")
    except EnvironmentError as e:
        logger.warning(f"Config warning: {e}")


@app.get("/", tags=["Health"])
async def root():
    return {"message": "IntelliAgents API is running", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/tasks/submit", response_model=TaskResponse, tags=["Tasks"])
async def submit_task(request: TaskRequest, background_tasks: BackgroundTasks):
    """Submit a new task for multi-agent processing."""
    if not request.task.strip():
        raise HTTPException(status_code=400, detail="Task cannot be empty.")

    task_id = memory.create_task(request.task)
    background_tasks.add_task(_run_workflow, task_id, request.task)

    return TaskResponse(
        task_id=task_id,
        status="pending",
        message=f"Task submitted successfully. Use task_id '{task_id}' to track progress.",
    )


@app.get("/tasks/{task_id}", response_model=TaskStatus, tags=["Tasks"])
async def get_task_status(task_id: str):
    """Get the current status and state of a task."""
    state = memory.get_state(task_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    return TaskStatus(
        task_id=task_id,
        task=state.get("task", ""),
        status=state.get("status", "unknown"),
        current_step=state.get("current_step"),
        report=state.get("report"),
        logs=state.get("logs", []),
        started_at=state.get("started_at"),
        completed_at=state.get("completed_at"),
        error=state.get("error"),
    )


@app.get("/tasks/{task_id}/logs", tags=["Tasks"])
async def stream_logs(task_id: str):
    """SSE endpoint: streams new log entries as they appear."""
    async def event_generator():
        last_count = 0
        for _ in range(300):  # poll for up to 5 minutes
            state = memory.get_state(task_id)
            if not state:
                yield {"data": '{"error": "Task not found"}'}
                break
            logs = state.get("logs", [])
            if len(logs) > last_count:
                for entry in logs[last_count:]:
                    yield {"data": str(entry)}
                last_count = len(logs)
            if state.get("status") in ("completed", "failed"):
                yield {"data": '{"done": true}'}
                break
            await asyncio.sleep(1)

    return EventSourceResponse(event_generator())


@app.get("/tasks", tags=["Tasks"])
async def list_tasks():
    """List all tasks with their status."""
    tasks = memory.list_tasks(limit=50)
    return {"tasks": tasks, "total": len(tasks)}


@app.get("/tasks/{task_id}/report", tags=["Tasks"])
async def get_report(task_id: str):
    """Get the final report for a completed task."""
    state = memory.get_state(task_id)
    if not state:
        raise HTTPException(status_code=404, detail="Task not found.")
    if state.get("status") != "completed":
        raise HTTPException(status_code=202, detail="Report not yet ready.")
    return {
        "task_id": task_id,
        "report": state.get("report", ""),
        "completed_at": state.get("completed_at"),
    }
