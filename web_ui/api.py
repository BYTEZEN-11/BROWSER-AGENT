from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import asyncio
import uuid
import json
import base64
from contextlib import asynccontextmanager
from datetime import datetime

from main import BrowserAgent, AgentConfig, load_config, graph
from playwright.async_api import async_playwright


# Global state for managing browser sessions
active_sessions: Dict[str, Dict[str, Any]] = {}


class TaskRequest(BaseModel):
    question: str = Field(..., description="The task/question for the agent")
    max_steps: Optional[int] = Field(None, description="Maximum steps for the agent")
    config_overrides: Optional[Dict[str, Any]] = Field(None, description="Configuration overrides")


class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatus(BaseModel):
    task_id: str
    status: str
    current_step: int
    max_steps: int
    current_action: Optional[str] = None
    current_args: Optional[List[str]] = None
    screenshot: Optional[str] = None
    steps_history: List[Dict[str, Any]] = []
    final_answer: Optional[str] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str


class SessionInfo(BaseModel):
    session_id: str
    status: str
    created_at: str
    current_url: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown - close all active sessions
    for session_id, session in active_sessions.items():
        if session.get("agent"):
            await session["agent"].stop()
    active_sessions.clear()


app = FastAPI(
    title="Langraph Browser Agent API",
    description="API for controlling the vision-enabled web browsing agent",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_agent(config_overrides: Dict[str, Any] = None) -> BrowserAgent:
    config = load_config()
    if config_overrides:
        for key, value in config_overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)
    return BrowserAgent(config)


async def run_agent_task(task_id: str, question: str, max_steps: int, config_overrides: Dict = None):
    session = active_sessions[task_id]
    agent = create_agent(config_overrides)
    session["agent"] = agent
    
    try:
        await agent.start()
        session["status"] = "running"
        session["current_url"] = agent.page.url
        session["updated_at"] = datetime.utcnow().isoformat()
        
        event_stream = graph.astream(
            {
                "page": agent.page,
                "input": question,
                "scratchpad": [],
            },
            {"recursion_limit": max_steps or config.max_steps},
        )
        
        steps = []
        async for event in event_stream:
            if "agent" not in event:
                continue
                
            pred = event["agent"].get("prediction") or {}
            action = pred.get("action")
            action_input = pred.get("args")
            
            steps.append({
                "step": len(steps) + 1,
                "action": action,
                "args": action_input,
                "timestamp": datetime.utcnow().isoformat(),
            })
            
            session["current_step"] = len(steps)
            session["current_action"] = action
            session["current_args"] = action_input
            session["steps_history"] = steps
            session["updated_at"] = datetime.utcnow().isoformat()
            
            if "img" in event["agent"]:
                session["screenshot"] = event["agent"]["img"]
            
            if action and "ANSWER" in action:
                session["final_answer"] = action_input[0] if action_input else "Task completed"
                session["status"] = "completed"
                break
                
    except Exception as e:
        session["status"] = "error"
        session["error"] = str(e)
    finally:
        session["updated_at"] = datetime.utcnow().isoformat()


@app.post("/api/v1/tasks", response_model=TaskResponse)
async def create_task(request: TaskRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())[:8]
    
    active_sessions[task_id] = {
        "task_id": task_id,
        "status": "starting",
        "current_step": 0,
        "max_steps": request.max_steps or load_config().max_steps,
        "current_action": None,
        "current_args": None,
        "screenshot": None,
        "steps_history": [],
        "final_answer": None,
        "error": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "agent": None,
    }
    
    background_tasks.add_task(
        run_agent_task,
        task_id,
        request.question,
        request.max_steps,
        request.config_overrides,
    )
    
    return TaskResponse(
        task_id=task_id,
        status="starting",
        message="Task created and started in background",
    )


@app.get("/api/v1/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    if task_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Task not found")
    
    session = active_sessions[task_id]
    return TaskStatus(**session)


@app.delete("/api/v1/tasks/{task_id}")
async def stop_task(task_id: str):
    if task_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Task not found")
    
    session = active_sessions[task_id]
    if session.get("agent"):
        await session["agent"].stop()
    
    session["status"] = "stopped"
    session["updated_at"] = datetime.utcnow().isoformat()
    
    return {"message": "Task stopped", "task_id": task_id}


@app.get("/api/v1/tasks", response_model=List[TaskStatus])
async def list_tasks():
    return [TaskStatus(**session) for session in active_sessions.values()]


@app.websocket("/api/v1/tasks/{task_id}/ws")
async def websocket_task_updates(websocket: WebSocket, task_id: str):
    await websocket.accept()
    
    if task_id not in active_sessions:
        await websocket.send_json({"error": "Task not found"})
        await websocket.close()
        return
    
    session = active_sessions[task_id]
    last_step = 0
    
    try:
        while True:
            await asyncio.sleep(1)
            
            if session["current_step"] > last_step:
                await websocket.send_json({
                    "type": "step_update",
                    "task_id": task_id,
                    "step": session["current_step"],
                    "action": session["current_action"],
                    "args": session["current_args"],
                    "screenshot": session["screenshot"],
                })
                last_step = session["current_step"]
            
            if session["status"] in ["completed", "error", "stopped"]:
                await websocket.send_json({
                    "type": "task_complete",
                    "task_id": task_id,
                    "status": session["status"],
                    "final_answer": session.get("final_answer"),
                    "error": session.get("error"),
                })
                break
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"error": str(e)})
    finally:
        await websocket.close()


@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "active_sessions": len(active_sessions),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/v1/config")
async def get_config():
    config = load_config()
    return {
        "model": config.model,
        "max_tokens": config.max_tokens,
        "temperature": config.temperature,
        "max_steps": config.max_steps,
        "start_url": config.start_url,
        "headless": config.headless,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
