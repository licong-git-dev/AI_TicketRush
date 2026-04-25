import asyncio
import sys

# This is a workaround for a known issue with Playwright on Windows.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from pydantic import BaseModel
import uuid
from contextlib import asynccontextmanager

# Import the browser manager we created
from automation import browser_manager

# Define the Maoyan login URL
MAOYAN_LOGIN_URL = "https://maoyan.com/sso/login"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage the browser lifecycle with the FastAPI application lifecycle.
    """
    await browser_manager.launch()
    yield
    await browser_manager.close()

# Pass the lifespan manager to the FastAPI app
app = FastAPI(
    lifespan=lifespan,
    title="TicketRush 抢票助手 API",
    description="这是一个用于猫眼演唱会抢票的API文档。",
    version="0.1.0",
)

# --- Data Models ---
class StartRequest(BaseModel):
    url: str
    session: str # e.g., "2024-08-02 周五 19:00"
    price: str   # e.g., "580"
    quantity: int

# --- In-memory storage (for demonstration) ---
tasks = {}
logs = {}

@app.get("/")
def read_root():
    return {"message": "Welcome to the TicketRush API"}

@app.post("/api/login")
async def login():
    """
    Opens the Maoyan login page in the browser.
    The user needs to manually scan the QR code to log in.
    """
    try:
        await browser_manager.go_to(MAOYAN_LOGIN_URL)
        return {"message": "Login page opened. Please scan the QR code to log in."}
    except Exception as e:
        # Stop the server from crashing if the browser fails
        return {"error": f"Failed to open login page: {str(e)}"}

@app.post("/api/start")
async def start_task(request: StartRequest):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "pending", "details": request.dict()}
    logs[task_id] = ["Task created."]
    # Placeholder: Here we would start the actual Playwright automation
    print(f"Task {task_id} created for {request.url}")
    return {"task_id": task_id}

@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    task = tasks.get(task_id)
    if not task:
        return {"error": "Task not found"}
    return {"task_id": task_id, "status": task.get("status")}

@app.get("/api/logs/{task_id}")
async def get_logs(task_id: str):
    log_messages = logs.get(task_id)
    if not log_messages:
        return {"error": "Task not found"}
    return {"task_id": task_id, "logs": log_messages}

# We will add the ticket grabbing logic here later. 