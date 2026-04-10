import sqlite3
import json

db_path = "intelliagents.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get the latest completed task
cursor.execute("SELECT task_id, task, state_json FROM tasks WHERE status = 'completed' ORDER BY updated_at DESC LIMIT 1;")
row = cursor.fetchone()

if row:
    task_id, task_text, state_json = row
    state = json.loads(state_json)
    report = state.get("report", "No report found in state.")
    print(f"Task ID: {task_id}")
    print(f"Task: {task_text}")
    print("-" * 20)
    print(report)
else:
    print("No completed tasks found in database.")

conn.close()
