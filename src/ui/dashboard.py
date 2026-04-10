"""
IntelliAgents — Streamlit Dashboard
Pixel-perfect implementation matching the provided UI mockup.
Connects to the FastAPI backend for live task execution.
"""
import sys
import os
import time
import json
from datetime import datetime

import streamlit as st
import httpx
import psutil
from datetime import datetime, date
from io import BytesIO
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IntelliAgents",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE = os.getenv("INTELLIAGENTS_API_URL", "http://localhost:8000")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Global ── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #0d1117; color: #e6edf3; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #161b22 !important;
    border-right: 1px solid #30363d;
}
[data-testid="stSidebar"] .stRadio label {
    color: #8b949e !important;
    font-size: 0.9rem;
    padding: 6px 12px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
}
[data-testid="stSidebar"] .stRadio label:hover { background: #21262d; color: #e6edf3 !important; }

/* ── Metric Cards ── */
.metric-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 20px;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
}
.metric-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.4); }
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #238636, #1f6feb);
}
.metric-label { font-size: 0.78rem; color: #8b949e; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }
.metric-value { font-size: 2rem; font-weight: 700; color: #e6edf3; line-height: 1; }
.metric-delta { font-size: 0.78rem; margin-top: 6px; }
.metric-delta.positive { color: #3fb950; }
.metric-delta.info { color: #58a6ff; }

/* ── Section Cards ── */
.section-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
}
.section-title {
    font-size: 1rem;
    font-weight: 600;
    color: #e6edf3;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ── Quick chips ── */
.chip-container { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
.chip {
    display: inline-block;
    background: #21262d;
    border: 1px solid #30363d;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.78rem;
    color: #8b949e;
    cursor: pointer;
    transition: all 0.2s;
}
.chip:hover { background: #30363d; color: #e6edf3; border-color: #58a6ff; }

/* ── Agent nodes ── */
.agent-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 16px; }
.agent-node {
    background: #21262d;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 12px 8px;
    text-align: center;
    transition: all 0.3s;
}
.agent-node.active { border-color: #3fb950; background: #0d2818; }
.agent-node.waiting { border-color: #e3b341; background: #2d2000; }
.agent-node.idle { border-color: #30363d; }
.agent-avatar {
    width: 44px; height: 44px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.85rem; font-weight: 700; margin: 0 auto 8px;
    color: white;
}
.avatar-or { background: linear-gradient(135deg, #6e40c9, #9e5cf7); }
.avatar-re { background: linear-gradient(135deg, #1a7f64, #3fb950); }
.avatar-an { background: linear-gradient(135deg, #b76e00, #e3b341); }
.avatar-wr { background: linear-gradient(135deg, #0969da, #58a6ff); }
.avatar-cr { background: linear-gradient(135deg, #cf222e, #f85149); }
.agent-name { font-size: 0.8rem; font-weight: 600; color: #e6edf3; }
.agent-status-badge {
    display: inline-block;
    font-size: 0.65rem; font-weight: 600;
    padding: 2px 8px; border-radius: 20px; margin-top: 4px;
}
.badge-active { background: #0d2818; color: #3fb950; border: 1px solid #238636; }
.badge-waiting { background: #2d2000; color: #e3b341; border: 1px solid #9e6a03; }
.badge-idle { background: #21262d; color: #8b949e; border: 1px solid #30363d; }

/* ── Progress bars ── */
.progress-row { margin-bottom: 12px; }
.progress-label {
    display: flex; justify-content: space-between;
    font-size: 0.8rem; margin-bottom: 5px;
    color: #8b949e;
}
.progress-label span:last-child { color: #e6edf3; font-weight: 600; }
.progress-track {
    height: 6px; background: #21262d; border-radius: 3px; overflow: hidden;
}
.progress-fill {
    height: 100%; border-radius: 3px;
    transition: width 0.4s ease;
}
.progress-done { background: linear-gradient(90deg, #238636, #3fb950); }
.progress-active { background: linear-gradient(90deg, #0969da, #58a6ff); animation: pulse-bar 1.5s ease-in-out infinite; }
.progress-pending { background: #30363d; }
@keyframes pulse-bar { 0%,100% { opacity: 1; } 50% { opacity: 0.6; } }

/* ── Specific Fix for Sidebar/Buttons ── */
.stButton > button[kind="secondary"] {
    background: #21262d !important;
    color: #8b949e !important;
    border: 1px solid #30363d !important;
}
.stButton > button[kind="secondary"]:hover {
    background: #30363d !important;
    color: #e6edf3 !important;
    border-color: #58a6ff !important;
}

/* ── Task queue items ── */
.task-item {
    display: flex; justify-content: space-between; align-items: flex-start;
    padding: 12px; background: #21262d; border-radius: 8px; margin-bottom: 8px;
    border-left: 3px solid transparent;
    transition: transform 0.2s;
}
.task-item:hover { transform: translateX(2px); }
.task-item.inprogress { border-left-color: #58a6ff; }
.task-item.queued { border-left-color: #e3b341; }
.task-item.done { border-left-color: #3fb950; }
.task-name { font-size: 0.85rem; font-weight: 600; color: #e6edf3; }
.task-desc { font-size: 0.75rem; color: #8b949e; margin-top: 2px; }
.task-badge {
    font-size: 0.65rem; font-weight: 600; padding: 2px 8px;
    border-radius: 20px; white-space: nowrap;
}
.badge-inprogress { background: #0c2d6b; color: #58a6ff; }
.badge-queued { background: #2d2000; color: #e3b341; }
.badge-done { background: #0d2818; color: #3fb950; }

/* ── Log console ── */
.log-console {
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 12px;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 0.75rem;
    height: 280px;
    overflow-y: auto;
    line-height: 1.6;
}
.log-line { margin-bottom: 2px; }
.log-time { color: #6e7681; }
.log-agent-or { color: #9e5cf7; font-weight: 700; }
.log-agent-re { color: #3fb950; font-weight: 700; }
.log-agent-an { color: #e3b341; font-weight: 700; }
.log-agent-wr { color: #58a6ff; font-weight: 700; }
.log-agent-cr { color: #f85149; font-weight: 700; }
.log-msg { color: #c9d1d9; }

/* ── Status pill ── */
.status-running {
    display: inline-flex; align-items: center; gap: 6px;
    background: #0d2818; color: #3fb950; font-size: 0.75rem;
    padding: 4px 12px; border-radius: 20px; border: 1px solid #238636;
    font-weight: 600;
}
.pulse-dot {
    width: 8px; height: 8px; border-radius: 50%; background: #3fb950;
    animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse { 0%,100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.5; transform: scale(0.75); } }

/* ── Run button / Primary ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #238636, #1a7f64) !important;
    color: white !important; border: none !important;
    padding: 10px 24px !important; border-radius: 8px !important;
    font-weight: 600 !important; font-size: 0.9rem !important;
    transition: all 0.2s !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #2ea043, #238636) !important;
    box-shadow: 0 4px 12px rgba(46,160,67,0.4) !important;
    transform: translateY(-1px) !important;
}

/* ── Report output ── */
.report-box {
    background: #0d1117; border: 1px solid #30363d; border-radius: 10px;
    padding: 24px; max-height: 600px; overflow-y: auto;
    font-size: 0.88rem; line-height: 1.7; color: #c9d1d9;
}

/* ── System badge ── */
.system-status {
    background: #0d2818; color: #3fb950;
    padding: 4px 10px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 600;
    border: 1px solid #238636;
}
</style>
""", unsafe_allow_html=True)



# ── API Helpers ───────────────────────────────────────────────────────────────
def api_submit_task(task: str):
    try:
        r = httpx.post(f"{API_BASE}/tasks/submit", json={"task": task}, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def api_get_status(task_id: str):
    try:
        r = httpx.get(f"{API_BASE}/tasks/{task_id}", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def api_list_tasks():
    try:
        r = httpx.get(f"{API_BASE}/tasks", timeout=10)
        r.raise_for_status()
        return r.json().get("tasks", [])
    except Exception:
        return []


def check_api_health():
    try:
        r = httpx.get(f"{API_BASE}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def generate_report_pdf(title, content):
    """Generate a PDF from report content using fpdf2."""
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(10)
    
    # Body
    pdf.set_font("helvetica", "", 11)
    # Basic markdown stripping/formatting for PDF
    clean_content = content.replace("#", "").replace("**", "").replace("*", "")
    pdf.multi_cell(0, 10, clean_content)
    
    # Return as bytes for Streamlit download_button
    pdf_bytes = pdf.output()
    return bytes(pdf_bytes) if isinstance(pdf_bytes, bytearray) else pdf_bytes

# ── Session State Init ─────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "page": "Dashboard",
        "task_input": "",
        "current_task_id": None,
        "task_status": "idle",       # idle | running | completed | failed
        "task_logs": [],
        "task_report": "",
        "history": [],
        "tasks_completed": 0,
        "tasks_today": 0,
        "avg_completion": "0.6m",
        "avg_delta": "0% faster",
        "system_load": "Low",
        "system_status": "All agents stable",
        "active_agents_count": "0 / 4",
        "active_agents_label": "0 idle",
        "poll_counter": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def refresh_metrics():
    """Fetch task history and calculate dashboard metrics."""
    tasks = api_list_tasks()
    
    # 1. Tasks Completed
    completed_tasks = [t for t in tasks if t.get("status") == "completed"]
    st.session_state.tasks_completed = len(completed_tasks)
    
    today_str = date.today().isoformat()
    tasks_today = [t for t in completed_tasks if t.get("completed_at", "").startswith(today_str)]
    st.session_state.tasks_today = len(tasks_today)
    
    # 2. Avg Completion
    total_duration = 0
    count = 0
    for t in completed_tasks:
        try:
            start = datetime.fromisoformat(t.get("started_at"))
            end = datetime.fromisoformat(t.get("completed_at"))
            duration = (end - start).total_seconds()
            if duration > 0:
                total_duration += duration
                count += 1
        except:
            continue
            
    if count > 0:
        avg_min = (total_duration / count) / 60
        st.session_state.avg_completion = f"{avg_min:.1f}m"
        improvement = ((5.0 - avg_min) / 5.0) * 100 if avg_min < 5.0 else 0
        st.session_state.avg_delta = f"↓ {int(improvement)}% faster" if improvement > 0 else "Optimal"
    else:
        st.session_state.avg_completion = "1.2m"
        st.session_state.avg_delta = "Optimal"

    # 3. System Load
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    load_val = max(cpu, ram)
    if load_val < 30:
        st.session_state.system_load = "Low"
        st.session_state.system_status = "All agents stable"
    elif load_val < 70:
        st.session_state.system_load = "Med"
        st.session_state.system_status = "System busy"
    else:
        st.session_state.system_load = "High"
        st.session_state.system_status = "Heavy load"

    # 4. Active Agents
    is_running = st.session_state.task_status == "running"
    if is_running and st.session_state.task_logs:
        recent_agents = set()
        for log in st.session_state.task_logs[-10:]:
            short = log.get("agent_short", "")[:2]
            if short in ["OR", "RE", "AN", "WR"]:
                recent_agents.add(short)
        active_n = len(recent_agents)
        st.session_state.active_agents_count = f"{active_n} / 4"
        st.session_state.active_agents_label = "running" if active_n > 0 else "initializing"
    else:
        st.session_state.active_agents_count = "0 / 4"
        st.session_state.active_agents_label = "System idle"

init_session()
refresh_metrics()


# ── Dialogs ──────────────────────────────────────────────────────────────────
@st.dialog("Report Viewer", width="large")
def show_task_report_dialog(task_id, task_title):
    with st.spinner("🔍 Fetching report details..."):
        data = api_get_status(task_id)
        if data.get("error"):
            st.error(f"Failed to load task: {data['error']}")
        else:
            st.markdown(f"### 📄 {task_title}")
            st.markdown(f"<span style='color:#8b949e;font-size:0.8rem;'>Task ID: {task_id}</span>", unsafe_allow_html=True)
            st.markdown("---")
            
            report_text = data.get("report", "")
            if not report_text:
                if data.get("status") == "completed":
                    st.warning("This task is completed but has no report text.")
                elif data.get("status") == "failed":
                    st.error(f"Task failed: {data.get('error', 'Unknown error')}")
                else:
                    st.info(f"Task is currently {data.get('status')}. No report yet.")
            else:
                st.markdown(report_text)
                st.markdown("---")
                
                pdf_bytes = generate_report_pdf(f"Report: {task_title[:50]}", report_text)
                st.download_button(
                    "⬇ Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"report_{task_id[:8]}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"dlg_dl_{task_id}",
                    type="primary"
                )

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;padding:8px 0 20px 0;">
        <div style="background:linear-gradient(135deg,#238636,#1f6feb);width:36px;height:36px;
             border-radius:8px;display:flex;align-items:center;justify-content:center;
             font-size:1.1rem;">🤖</div>
        <div>
            <div style="font-weight:700;font-size:1rem;color:#e6edf3;">IntelliAgents</div>
            <div style="font-size:0.7rem;color:#8b949e;">Multi-Agent AI System</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    nav_options = ["Dashboard", "Agents", "History", ]
    nav_icons = {"Dashboard": "⊞", "Agents": "👤",  "History": "🕐", }

    for opt in nav_options:
        selected = st.session_state.page == opt
        if st.button(
            f"{nav_icons[opt]}  {opt}",
            key=f"nav_{opt}",
            use_container_width=True,
            type="primary" if selected else "secondary"
        ):
            st.session_state.page = opt
            st.rerun()

    st.markdown("---")
    

# ── Page: Dashboard ──────────────────────────────────────────────────────────
if st.session_state.page == "Dashboard":

    # Header
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown("<h1 style='color:#e6edf3;font-size:1.6rem;font-weight:700;margin:0;'>Dashboard</h1>", unsafe_allow_html=True)
    with col_h2:
        api_ok = check_api_health()
        status_text = "● System running" if api_ok else "● API offline"
        status_color = "#3fb950" if api_ok else "#f85149"
        st.markdown(
            f"<div style='text-align:right;'><span style='background:#0d2818;color:{status_color};"
            f"padding:5px 12px;border-radius:20px;font-size:0.78rem;font-weight:600;"
            f"border:1px solid {status_color};'>{status_text}</span></div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-bottom:20px'/>", unsafe_allow_html=True)

    # ── Metric Cards ──
    tasks_done = st.session_state.tasks_completed

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Tasks Completed</div>
            <div class="metric-value">{st.session_state.tasks_completed}</div>
        </div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Avg. Completion</div>
            <div class="metric-value">{st.session_state.avg_completion}</div>
        </div>""", unsafe_allow_html=True)
        # <div class="metric-delta info">{st.session_state.avg_delta}</div>
    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">System Load</div>
            <div class="metric-value">{st.session_state.system_load}</div>
        </div>""", unsafe_allow_html=True)
            # <div class="metric-delta info">{st.session_state.system_status}</div>
        
    with m4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Active Agents</div>
            <div class="metric-value">{st.session_state.active_agents_count}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:20px'/>", unsafe_allow_html=True)


    # ── Main Layout: Left (task + agents) / Right (workflow + queue) ──
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        # ── Task Submission ──
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📤 Submit a task</div>', unsafe_allow_html=True)

        task_input = st.text_area(
            "Task Description",
            value=st.session_state.task_input,
            placeholder="e.g. Analyze the current state of renewable energy in Southeast Asia...",
            height=90,
            key="task_textarea",
            label_visibility="collapsed",
        )

        EXAMPLE_TASKS = [
            "Renewable energy in SEA",
            "Compare top 5 PM tools",
            "Document this Python codebase",
            "Analyze sales CSV for trends",
        ]

        st.markdown('<div style="margin-top:10px;"><span style="font-size:0.75rem;color:#8b949e;">Quick examples:</span></div>', unsafe_allow_html=True)

        ecols = st.columns(len(EXAMPLE_TASKS))
        for i, ex in enumerate(EXAMPLE_TASKS):
            with ecols[i]:
                if st.button(ex, key=f"ex_{i}", use_container_width=True):
                    st.session_state.task_input = ex
                    st.rerun()

        col_run1, col_run2 = st.columns([3, 1])
        with col_run2:
            run_clicked = st.button("Run ↗", key="run_btn", use_container_width=True, type="primary")

        if run_clicked:
            final_task = task_input or st.session_state.task_input
            if not final_task.strip():
                st.error("Please enter a task description.")
            elif not check_api_health():
                st.error("⚠️ API is offline. Start the backend first: `python run.py --api`")
            else:
                result = api_submit_task(final_task)
                if "error" in result:
                    st.error(f"Submission failed: {result['error']}")
                else:
                    st.session_state.current_task_id = result["task_id"]
                    st.session_state.task_status = "running"
                    st.session_state.task_logs = []
                    st.session_state.task_report = ""
                    # st.session_state.task_critique = {}
                    st.session_state.task_input = final_task
                    st.session_state.poll_counter = 0
                    st.success(f"✅ Task submitted! ID: `{result['task_id'][:8]}...`")
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        # ── Agent Activity ──
        task_status = st.session_state.task_status
        current_logs = st.session_state.task_logs
        current_step_agents = set()
        if current_logs:
            last_agents = [l.get("agent_short", "") for l in current_logs[-3:]]
            current_step_agents = set(last_agents)

        def agent_state(shortcode: str) -> str:
            if task_status != "running":
                return "idle"
            if shortcode in current_step_agents:
                return "active"
            return "idle"

        agents_cfg = [
            ("OR", "Orchestrator", "avatar-or"),
            ("RE", "Researcher", "avatar-re"),
            ("AN", "Analyst", "avatar-an"),
            ("WR", "Writer", "avatar-wr"),
        ]

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🤖 Agent activity</div>', unsafe_allow_html=True)

        agent_html = '<div class="agent-grid">'
        for short, name, avatar_cls in agents_cfg:
            state_cls = agent_state(short)
            badge_cls = f"badge-{state_cls}"
            badge_label = state_cls.capitalize()
            agent_html += f"""
            <div class="agent-node {state_cls}">
                <div class="agent-avatar {avatar_cls}">{short}</div>
                <div class="agent-name">{name}</div>
                <span class="agent-status-badge {badge_cls}">{badge_label}</span>
            </div>"""
        agent_html += '</div>'
        st.markdown(agent_html, unsafe_allow_html=True)

        # ── Agent Log Console ──
        st.markdown('<div style="margin-top:12px;"><div class="section-title" style="font-size:0.85rem;">📋 Agent logs</div>', unsafe_allow_html=True)

        log_color_map = {"OR": "log-agent-or", "RE": "log-agent-re", "AN": "log-agent-an", "WR": "log-agent-wr"}

        log_lines = []
        for entry in current_logs[-30:]:
            ts = entry.get("timestamp", "")
            short = entry.get("agent_short", "SYS")[:4]
            msg = entry.get("message", "")
            agent_cls = log_color_map.get(short[:2], "log-agent-or")
            log_lines.append(
                f'<div class="log-line"><span class="log-time">{ts}</span> '
                f'<span class="{agent_cls}">[{short}]</span> '
                f'<span class="log-msg">{msg}</span></div>'
            )

        if not log_lines:
            log_lines = ['<div class="log-line"><span class="log-time">--:--:--</span> <span class="log-msg" style="color:#6e7681;">Waiting for task submission...</span></div>']

        log_html = f'<div class="log-console">{"".join(log_lines)}</div>'
        st.markdown(log_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        # ── Workflow Progress ──
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📊 Workflow progress</div>', unsafe_allow_html=True)

        workflow_steps = [
            ("Task decomposition", "OR"),
            ("Research & data gathering", "RE"),
            ("Analysis", "AN"),
            ("Writing", "WR"),
        ]

        def get_step_progress(agent_short: str) -> tuple:
            """Return (pct, css_class) for a given agent."""
            if task_status == "idle":
                return (0, "progress-pending")
            if task_status == "completed":
                return (100, "progress-done")
            # Check if this agent has appeared in logs
            appeared = any(l.get("agent_short", "")[:2] == agent_short[:2] for l in current_logs)
            if not appeared:
                return (0, "progress-pending")
            # Check if currently active
            is_active = agent_short[:2] in current_step_agents
            if is_active:
                return (55, "progress-active")
            return (100, "progress-done")

        for step_name, agent_short in workflow_steps:
            pct, css_cls = get_step_progress(agent_short)
            st.markdown(f"""
            <div class="progress-row">
                <div class="progress-label">
                    <span>{step_name}</span>
                    <span>{"Done" if pct == 100 else (f"{pct}%" if pct > 0 else "—")}</span>
                </div>
                <div class="progress-track">
                    <div class="progress-fill {css_cls}" style="width:{pct}%"></div>
                </div>
            </div>""", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # ── Task Queue ──
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📋 Task queue</div>', unsafe_allow_html=True)

        history_tasks = api_list_tasks()

        if not history_tasks:
            st.markdown('<div style="color:#6e7681;font-size:0.85rem;text-align:center;padding:20px;">No tasks yet. Submit your first task!</div>', unsafe_allow_html=True)
        else:
            for t in history_tasks[:5]:
                status = t.get("status", "pending")
                state_map = {
                    "running": ("inprogress", "badge-inprogress", "In progress"),
                    "pending": ("queued", "badge-queued", "Queued"),
                    "completed": ("done", "badge-done", "Done"),
                    "failed": ("inprogress", "badge-inprogress", "Failed"),
                }
                item_cls, badge_cls, badge_label = state_map.get(status, ("queued", "badge-queued", status.capitalize()))
                task_text = t.get("task", "")
                short_task = task_text[:30] + ("..." if len(task_text) > 30 else "")
                created = t.get("created_at", "")[:16].replace("T", " ")
                col_t1, col_t2 = st.columns([4, 1])
                with col_t1:
                    st.markdown(f"""
                    <div class="task-item {item_cls}">
                        <div>
                            <div class="task-name">{short_task}</div>
                            <div class="task-desc">{created}</div>
                        </div>
                        <span class="task-badge {badge_cls}">{badge_label}</span>
                    </div>""", unsafe_allow_html=True)
                with col_t2:
                    if status == "completed":
                        if st.button("View", key=f"view_{t['task_id']}"):
                            # Fetch details for this task
                            with st.spinner("🔍 Fetching report from server..."):
                                data = api_get_status(t['task_id'])
                                if data.get("error") and isinstance(data["error"], str):
                                    st.error(f"Failed to load task: {data['error']}")
                                elif not data.get("report") and data.get("status") == "completed":
                                    st.warning("This task was marked done but has no report text.")
                                elif data.get("status") == "failed":
                                    st.error(f"Task execution failed: {data.get('error', 'Unknown error')}")
                                else:
                                    st.session_state.current_task_id = t['task_id']
                                    st.session_state.task_report = data.get("report", "")
                                    st.session_state.task_status = data.get("status", "completed")
                                    st.session_state.task_input = t['task']
                                    st.session_state.task_logs = data.get("logs", [])
                                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # ── Report Display (Prominent Full Width) ──
    if st.session_state.task_report:
        st.markdown(f"""
        <div class="section-card" style="border-top: 4px solid #3fb950; background: #0d1117;">
            <div class="section-title">📄 Selected Report: {st.session_state.task_input}</div>
        </div>""", unsafe_allow_html=True)
        
        with st.expander("📚 Click to View Full Report", expanded=True):
            st.markdown(st.session_state.task_report)
            st.markdown("---")
            
            pdf_bytes = generate_report_pdf(f"Report: {st.session_state.task_input[:50]}", st.session_state.task_report)
            st.download_button(
                "⬇ Download PDF Report",
                data=pdf_bytes,
                file_name=f"report_{st.session_state.current_task_id[:8] if st.session_state.current_task_id else 'task'}.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
        st.markdown("<div style='margin-bottom:20px'/>", unsafe_allow_html=True)

    # ── Live Polling ──────────────────────────────────────────────────────────
    if st.session_state.task_status == "running" and st.session_state.current_task_id:
        state_data = api_get_status(st.session_state.current_task_id)
        if "error" not in state_data:
            st.session_state.task_logs = state_data.get("logs", [])
            status = state_data.get("status", "running")
            if status in ("completed", "failed"):
                st.session_state.task_status = status
                st.session_state.task_report = state_data.get("report", "")
                if status == "completed":
                    st.session_state.tasks_completed += 1
                    st.balloons()
        time.sleep(2)
        st.rerun()

# ── Page: Agents ──────────────────────────────────────────────────────────────
elif st.session_state.page == "Agents":
    st.markdown("<h1 style='color:#e6edf3;font-size:1.6rem;font-weight:700;'>Agents</h1>", unsafe_allow_html=True)

    agents_info = [
        {
            "name": "Orchestrator", "short": "OR", "color": "linear-gradient(135deg,#6e40c9,#9e5cf7)",
            "role": "Task Decomposition & Coordination",
            "description": "Receives the user task, analyzes complexity, and breaks it into atomic subtasks assigned to specialists. Manages workflow state and aggregates results.",
            "capabilities": ["Task decomposition", "DAG generation", "Agent routing", "State management"],
        },
        {
            "name": "Researcher", "short": "RE", "color": "linear-gradient(135deg,#1a7f64,#3fb950)",
            "role": "Information Gathering",
            "description": "Performs targeted web searches using DuckDuckGo, extracts relevant information, and synthesizes findings into structured research reports.",
            "capabilities": ["Web search (DuckDuckGo)", "Document loading", "Source citation", "Fact extraction"],
        },
        {
            "name": "Analyst", "short": "AN", "color": "linear-gradient(135deg,#b76e00,#e3b341)",
            "role": "Data Analysis & Insights",
            "description": "Processes research data to identify patterns, trends, and statistical insights. Performs comparative analysis and generates strategic recommendations.",
            "capabilities": ["Pattern recognition", "Trend analysis", "Comparative analysis", "CSV/data processing"],
        },
        {
            "name": "Writer", "short": "WR", "color": "linear-gradient(135deg,#0969da,#58a6ff)",
            "role": "Report Synthesis",
            "description": "Synthesizes research and analysis into comprehensive, professional Pdf reports.",
            "capabilities": ["Report writing", "Markdown formatting", "Source citation", "Iterative revision"],
        },
    ]

    for agent in agents_info:
        st.markdown(f"""
        <div class="section-card" style="display:flex;gap:16px;align-items:flex-start;">
            <div style="background:{agent['color']};width:52px;height:52px;border-radius:12px;
                 display:flex;align-items:center;justify-content:center;font-size:1.1rem;
                 font-weight:700;color:white;flex-shrink:0;">{agent['short']}</div>
            <div style="flex:1;">
                <div style="font-size:1rem;font-weight:700;color:#e6edf3;">{agent['name']}</div>
                <div style="font-size:0.78rem;color:#58a6ff;margin-bottom:8px;">{agent['role']}</div>
                <div style="font-size:0.82rem;color:#8b949e;margin-bottom:12px;">{agent['description']}</div>
                <div style="display:flex;flex-wrap:wrap;gap:6px;">
                    {''.join(f'<span style="background:#21262d;border:1px solid #30363d;padding:3px 10px;border-radius:20px;font-size:0.72rem;color:#c9d1d9;">{cap}</span>' for cap in agent['capabilities'])}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── Page: History ─────────────────────────────────────────────────────────────
elif st.session_state.page == "History":
    st.markdown("<h1 style='color:#e6edf3;font-size:1.6rem;font-weight:700;'>History</h1>", unsafe_allow_html=True)
    tasks = api_list_tasks()
    if not tasks:
        st.info("No task history yet.")
    else:
        st.markdown(f'<div style="color:#8b949e;font-size:0.85rem;margin-bottom:12px;">{len(tasks)} total tasks</div>', unsafe_allow_html=True)
        for t in tasks:
            tid = t.get("task_id", "unknown")
            status = t.get("status", "unknown")
            task_text = t.get("task", "No description")
            created = t.get("created_at", "")[:16].replace("T", " ")
            color = {"completed": "#3fb950", "running": "#58a6ff", "failed": "#f85149", "pending": "#e3b341"}.get(status, "#8b949e")
            
            with st.container():
                c1, c2, c3, c4 = st.columns([2.5, 1, 0.6, 0.6], vertical_alignment="center")
                with c1:
                    st.markdown(f"""
                    <div style="font-size:0.88rem;font-weight:600;color:#e6edf3;">{task_text[:100]}{"..." if len(task_text)>100 else ""}</div>
                    <div style="font-size:0.75rem;color:#6e7681;margin-top:4px;">
                        <span>📅 {created}</span> &nbsp;|&nbsp; <span>🔑 {tid[:12]}...</span>
                    </div>
                    """, unsafe_allow_html=True)
                with c2:
                    st.markdown(f"""
                    <div style="text-align:center;">
                        <span style="color:{color};font-size:0.75rem;font-weight:600;border:1px solid {color};padding:2px 10px;border-radius:20px;">
                            {status.upper()}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                with c3:
                    if status == "completed":
                        if st.button("View", key=f"hist_v_{tid}", use_container_width=True):
                            show_task_report_dialog(tid, task_text)
                with c4:
                    if status == "completed":
                        dl_key = f"ready_dl_hist_{tid}"
                        if dl_key not in st.session_state:
                            if st.button("DL", key=f"hist_dl_init_{tid}", use_container_width=True):
                                with st.spinner("..."):
                                    data = api_get_status(tid)
                                    if data.get("error"):
                                        st.error(f"Download failed: {data['error']}")
                                    else:
                                        st.session_state[dl_key] = data.get("report", "No content")
                                        st.rerun()
                        else:
                            pdf_bytes = generate_report_pdf(f"Report: {task_text[:50]}", st.session_state[dl_key])
                            st.download_button(
                                "💾 PDF", 
                                data=pdf_bytes, 
                                file_name=f"report_{tid[:8]}.pdf", 
                                key=f"hist_dl_save_{tid}",
                                use_container_width=True,
                                type="primary"
                            )
                st.markdown("<hr style='margin:10px 0; border:0; border-top:1px solid #21262d;'>", unsafe_allow_html=True)
