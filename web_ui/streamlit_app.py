import streamlit as st
import requests
import asyncio
import websockets
import json
import base64
from PIL import Image
from io import BytesIO
import time
from datetime import datetime
from typing import Optional
import threading
import queue

# Page config
st.set_page_config(
    page_title="Langraph Browser Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# API Base URL
API_BASE = "http://localhost:8000/api/v1"

# Session state initialization
if "task_id" not in st.session_state:
    st.session_state.task_id = None
if "task_status" not in st.session_state:
    st.session_state.task_status = None
if "ws_queue" not in st.session_state:
    st.session_state.ws_queue = queue.Queue()
if "ws_thread" not in st.session_state:
    st.session_state.ws_thread = None
if "stop_ws" not in st.session_state:
    st.session_state.stop_ws = False


def start_websocket_listener(task_id: str):
    """Start WebSocket listener in background thread."""
    def run_ws():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(ws_listener(task_id))
    
    thread = threading.Thread(target=run_ws, daemon=True)
    thread.start()
    st.session_state.ws_thread = thread


async def ws_listener(task_id: str):
    """WebSocket listener for real-time updates."""
    uri = f"ws://localhost:8000/api/v1/tasks/{task_id}/ws"
    try:
        async with websockets.connect(uri) as websocket:
            while not st.session_state.stop_ws:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    st.session_state.ws_queue.put(data)
                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    break
    except Exception as e:
        st.session_state.ws_queue.put({"error": str(e)})


def poll_task_status(task_id: str) -> dict:
    """Poll task status via REST API."""
    try:
        response = requests.get(f"{API_BASE}/tasks/{task_id}", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None


def create_task(question: str, max_steps: int, config_overrides: dict) -> Optional[str]:
    """Create a new task."""
    try:
        response = requests.post(
            f"{API_BASE}/tasks",
            json={
                "question": question,
                "max_steps": max_steps,
                "config_overrides": config_overrides,
            },
            timeout=10,
        )
        if response.status_code == 200:
            return response.json()["task_id"]
    except Exception as e:
        st.error(f"Failed to create task: {e}")
    return None


def stop_task(task_id: str) -> bool:
    """Stop a running task."""
    try:
        response = requests.delete(f"{API_BASE}/tasks/{task_id}", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def get_all_tasks() -> list:
    """Get all tasks."""
    try:
        response = requests.get(f"{API_BASE}/tasks", timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return []


def display_screenshot(base64_img: str):
    """Display base64 encoded screenshot."""
    try:
        img_data = base64.b64decode(base64_img)
        img = Image.open(BytesIO(img_data))
        st.image(img, caption="Browser Screenshot", use_container_width=True)
    except Exception as e:
        st.error(f"Failed to display screenshot: {e}")


def main():
    st.title("🤖 Langraph Browser Agent")
    st.markdown("Vision-enabled web browsing agent powered by LLMs")
    
    # Sidebar - Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Model settings
        st.subheader("Model Settings")
        model = st.selectbox(
            "Model",
            ["gpt-4-turbo", "gpt-4o", "gpt-3.5-turbo"],
            index=0,
        )
        temperature = st.slider("Temperature", 0.0, 1.0, 0.1, 0.1)
        max_tokens = st.number_input("Max Tokens", 1024, 8192, 4096, 512)
        
        # Agent settings
        st.subheader("Agent Settings")
        max_steps = st.number_input("Max Steps", 10, 500, 150, 10)
        start_url = st.text_input("Start URL", "https://www.google.com")
        headless = st.checkbox("Headless Mode", value=False)
        wait_time = st.number_input("Wait Time (s)", 1, 30, 5)
        
        # Browser settings
        st.subheader("Browser Settings")
        screenshot_quality = st.slider("Screenshot Quality", 10, 100, 80)
        typing_delay_min = st.number_input("Typing Delay Min (s)", 0.01, 1.0, 0.08, 0.01)
        typing_delay_max = st.number_input("Typing Delay Max (s)", 0.01, 1.0, 0.15, 0.01)
        
        config_overrides = {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "max_steps": max_steps,
            "start_url": start_url,
            "headless": headless,
            "wait_time": wait_time,
            "screenshot_quality": screenshot_quality,
            "typing_delay_min": typing_delay_min,
            "typing_delay_max": typing_delay_max,
        }
        
        st.divider()
        
        # Task history
        st.subheader("📋 Task History")
        tasks = get_all_tasks()
        for task in tasks[-5:]:  # Show last 5
            status_emoji = {
                "starting": "🟡",
                "running": "🟢",
                "completed": "✅",
                "error": "❌",
                "stopped": "⏹️",
            }.get(task["status"], "❓")
            
            if st.button(f"{status_emoji} {task['task_id'][:8]} - {task['status']}", key=f"hist_{task['task_id']}"):
                st.session_state.task_id = task["task_id"]
                st.rerun()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 Chat Interface")
        
        # Task input
        if st.session_state.task_id is None:
            question = st.text_area(
                "Enter your task:",
                placeholder="e.g., Find the latest news on CNN and summarize in 30 words",
                height=100,
            )
            
            col_start, col_clear = st.columns([1, 1])
            with col_start:
                if st.button("🚀 Start Task", type="primary", use_container_width=True, disabled=not question.strip()):
                    task_id = create_task(question.strip(), max_steps, config_overrides)
                    if task_id:
                        st.session_state.task_id = task_id
                        st.session_state.stop_ws = False
                        start_websocket_listener(task_id)
                        st.rerun()
            
            with col_clear:
                if st.button("🗑️ Clear History", use_container_width=True):
                    st.session_state.task_id = None
                    st.rerun()
        
        # Task status display
        else:
            # Process WebSocket messages
            while not st.session_state.ws_queue.empty():
                msg = st.session_state.ws_queue.get()
                if msg.get("type") == "step_update":
                    st.session_state.task_status = poll_task_status(st.session_state.task_id)
                elif msg.get("type") == "task_complete":
                    st.session_state.task_status = poll_task_status(st.session_state.task_id)
                    st.session_state.stop_ws = True
            
            # Fallback polling
            if st.session_state.task_status is None:
                st.session_state.task_status = poll_task_status(st.session_state.task_id)
            
            if st.session_state.task_status:
                status = st.session_state.task_status
                
                # Status header
                status_colors = {
                    "starting": "🟡 Starting...",
                    "running": "🟢 Running",
                    "completed": "✅ Completed",
                    "error": "❌ Error",
                    "stopped": "⏹️ Stopped",
                }
                st.markdown(f"### {status_colors.get(status['status'], status['status'])}")
                
                # Progress bar
                progress = min(status["current_step"] / status["max_steps"], 1.0)
                st.progress(progress, text=f"Step {status['current_step']} / {status['max_steps']}")
                
                # Current action
                if status["current_action"]:
                    st.info(f"**Current Action:** {status['current_action']} {status['current_args'] or ''}")
                
                # Screenshot
                if status["screenshot"]:
                    display_screenshot(status["screenshot"])
                
                # Steps history
                if status["steps_history"]:
                    with st.expander("📜 Steps History", expanded=True):
                        for step in status["steps_history"]:
                            st.markdown(
                                f"**Step {step['step']}:** `{step['action']}` {step['args'] or ''} "
                                f"*({step['timestamp']})*"
                            )
                
                # Final answer
                if status["final_answer"]:
                    st.success(f"**Final Answer:** {status['final_answer']}")
                
                # Error
                if status["error"]:
                    st.error(f"**Error:** {status['error']}")
                
                # Control buttons
                col_stop, col_new = st.columns([1, 1])
                with col_stop:
                    if status["status"] in ["starting", "running"]:
                        if st.button("⏹️ Stop Task", type="secondary", use_container_width=True):
                            if stop_task(st.session_state.task_id):
                                st.session_state.stop_ws = True
                                st.session_state.task_status = poll_task_status(st.session_state.task_id)
                                st.rerun()
                
                with col_new:
                    if st.button("➕ New Task", use_container_width=True):
                        st.session_state.task_id = None
                        st.session_state.task_status = None
                        st.session_state.stop_ws = True
                        st.rerun()
                
                # Auto-refresh for running tasks
                if status["status"] in ["starting", "running"]:
                    time.sleep(2)
                    st.rerun()
    
    with col2:
        st.header("📊 Live Monitor")
        
        # Real-time metrics
        if st.session_state.task_status:
            status = st.session_state.task_status
            
            # Metrics
            m1, m2 = st.columns(2)
            with m1:
                st.metric("Steps", status["current_step"], f"/ {status['max_steps']}")
            with m2:
                elapsed = (
                    datetime.fromisoformat(status["updated_at"].replace("Z", "+00:00")) -
                    datetime.fromisoformat(status["created_at"].replace("Z", "+00:00"))
                ).total_seconds()
                st.metric("Elapsed", f"{elapsed:.0f}s")
            
            # Current URL
            if status.get("current_url"):
                st.markdown(f"**Current URL:** {status['current_url']}")
            
            # Live log
            st.subheader("📝 Live Log")
            log_container = st.container()
            with log_container:
                for step in status["steps_history"][-10:]:  # Show last 10
                    st.text(f"[{step['step']:3d}] {step['action']} {step['args'] or ''}")
        
        else:
            st.info("Start a task to see live monitoring")
        
        st.divider()
        
        # System info
        st.subheader("ℹ️ System Info")
        try:
            health = requests.get(f"{API_BASE}/health", timeout=2).json()
            st.json(health)
        except Exception:
            st.warning("API server not reachable")


if __name__ == "__main__":
    main()