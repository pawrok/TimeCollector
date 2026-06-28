import asyncio
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

# How long to wait after the last client disconnects before stopping timers.
# Long enough to survive a brief VPN/network hiccup; short enough that an
# intentionally closed tab doesn't keep the timer running forever.
STOP_GRACE_SECONDS = 120

connected_clients: set[WebSocket] = set()
_stop_task: asyncio.Task | None = None


async def _stop_after_grace(disconnected_at: datetime):
    await asyncio.sleep(STOP_GRACE_SECONDS)
    if not connected_clients:
        # Use the disconnection timestamp, not now(), so the grace period
        # itself is never counted as tracked time.
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

    # Cancel any pending stop — a client just (re)connected.
    if _stop_task and not _stop_task.done():
        _stop_task.cancel()
        _stop_task = None

    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        disconnected_at = datetime.now(timezone.utc)
        connected_clients.discard(websocket)
        if not connected_clients:
            _stop_task = asyncio.create_task(_stop_after_grace(disconnected_at))


_frontend_dist = os.getenv(
    "FRONTEND_DIST",
    os.path.join(os.path.dirname(__file__), "../../frontend/dist"),
)
if os.path.exists(_frontend_dist):
    app.mount("/", StaticFiles(directory=_frontend_dist, html=True), name="static")
