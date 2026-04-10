"""
Shared Memory — SQLite-backed context and task history store.
"""
import json
import logging
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from config.settings import SQLITE_DB_PATH

logger = logging.getLogger(__name__)

# ── Schema ──────────────────────────────────────────────────────────────────
_CREATE_TASKS_TABLE = """
CREATE TABLE IF NOT EXISTS tasks (
    task_id     TEXT PRIMARY KEY,
    task        TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending',
    state_json  TEXT,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
"""


class SharedMemory:
    """SQLite-backed store for persisting task state across the workflow."""

    def __init__(self, db_path: str = SQLITE_DB_PATH):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(_CREATE_TASKS_TABLE)
        logger.info(f"[SharedMemory] DB initialized at {self.db_path}")

    # ── Task CRUD ──────────────────────────────────────────────────────────

    def create_task(self, task: str) -> str:
        """Create a new task record and return its task_id."""
        task_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO tasks (task_id, task, status, created_at, updated_at) VALUES (?,?,?,?,?)",
                (task_id, task, "pending", now, now),
            )
        logger.info(f"[SharedMemory] Created task {task_id}")
        return task_id

    def update_state(self, task_id: str, state: Dict[str, Any]) -> None:
        """Persist the current workflow state for a task."""
        now = datetime.now().isoformat()
        status = state.get("status", "running")
        with self._conn() as conn:
            conn.execute(
                "UPDATE tasks SET state_json=?, status=?, updated_at=? WHERE task_id=?",
                (json.dumps(state, default=str), status, now, task_id),
            )

    def get_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the latest state for a task."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT state_json, status FROM tasks WHERE task_id=?", (task_id,)
            ).fetchone()
        if not row:
            return None
        state_json = row["state_json"]
        if not state_json:
            return {"status": row["status"]}
        return json.loads(state_json)

    def list_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return a list of all tasks (most recent first)."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT task_id, task, status, created_at, updated_at FROM tasks ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_logs(self, task_id: str) -> List[Dict[str, Any]]:
        """Extract logs from the task state."""
        state = self.get_state(task_id)
        if not state:
            return []
        return state.get("logs", [])


# Module-level singleton
memory = SharedMemory()
