import asyncio
import json
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session

from .database import create_db_and_tables, engine
from . import crud
from .routers import trackers, stats, export

STOP_GRACE_SECONDS = 3600         # 1 h  — network drop / crash / closed tab
BACKGROUND_GRACE_SECONDS = 14400  # 4 h  — intentional screen-off or tab background

connected_clients: set[WebSocket] = set()
_backgrounded: set[WebSocket] = set()  # clients that signalled going_background
_stop_task: asyncio.Task | None = None


async def _stop_after_grace(disconnected_at: datetime, grace: int):
    await asyncio.sleep(grace)
    if not connected_clients:
        with Session(engine) as db:
            crud.stop_all_sessions(db, end_time=disconnected_at)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trackers.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(export.router, prefix="/api")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global _stop_task

    if _stop_task and not _stop_task.done():
        _stop_task.cancel()
        _stop_task = None

    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                if json.loads(data).get("type") == "going_background":
                    _backgrounded.add(websocket)
            except (json.JSONDecodeError, AttributeError, ValueError):
                pass
    except WebSocketDisconnect:
        disconnected_at = datetime.now(timezone.utc)
        is_background = websocket in _backgrounded
        _backgrounded.discard(websocket)
        connected_clients.discard(websocket)
        if not connected_clients:
            grace = BACKGROUND_GRACE_SECONDS if is_background else STOP_GRACE_SECONDS
            _stop_task = asyncio.create_task(_stop_after_grace(disconnected_at, grace))


_frontend_dist = os.getenv(
    "FRONTEND_DIST",
    os.path.join(os.path.dirname(__file__), "../../frontend/dist"),
)
if os.path.exists(_frontend_dist):
    app.mount("/", StaticFiles(directory=_frontend_dist, html=True), name="static")
