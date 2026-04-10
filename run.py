"""
IntelliAgents — CLI entry point.
Usage:
    python run.py --api      # Start FastAPI backend
    python run.py --ui       # Start Streamlit dashboard
    python run.py --both     # Start both (in separate processes)
"""
import argparse
import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def start_api():
    print("Starting IntelliAgents FastAPI backend on http://localhost:8000 ...")
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "src.api.main:app",
         "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "warning"],
        cwd=BASE_DIR,
    )


def start_ui():
    print("Starting IntelliAgents Streamlit dashboard on http://localhost:8501 ...")
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", "src/ui/dashboard.py",
         "--server.port", "8501", "--server.headless", "true"],
        cwd=BASE_DIR,
    )


def start_both():
    import multiprocessing
    api_proc = multiprocessing.Process(target=start_api)
    ui_proc = multiprocessing.Process(target=start_ui)
    api_proc.start()
    import time; time.sleep(2)  # give API a head start
    ui_proc.start()
    print("Both services started!")
    print("   API: http://localhost:8000")
    print("   UI:  http://localhost:8501")
    try:
        api_proc.join()
        ui_proc.join()
    except KeyboardInterrupt:
        api_proc.terminate()
        ui_proc.terminate()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IntelliAgents launcher")
    parser.add_argument("--api", action="store_true", help="Start FastAPI backend")
    parser.add_argument("--ui", action="store_true", help="Start Streamlit dashboard")
    parser.add_argument("--both", action="store_true", help="Start both services")
    args = parser.parse_args()

    if args.both:
        start_both()
    elif args.api:
        start_api()
    elif args.ui:
        start_ui()
    else:
        parser.print_help()
        print("\nExample: python run.py --api")
