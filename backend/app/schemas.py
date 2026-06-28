from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TrackerCreate(BaseModel):
    name: str
    color: Optional[str] = None


class TrackerUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    sort_order: Optional[int] = None
    archived: Optional[bool] = None


class TrackerRead(BaseModel):
    id: int
    name: str
    color: str
    sort_order: int
    archived: bool
    created_at: datetime
    is_running: bool
    running_since: Optional[datetime]
    today_completed_seconds: float
    total_seconds: float


class DailyStat(BaseModel):
    date: str
    tracker_id: int
    tracker_name: str
    color: str
    seconds: float


class TotalStat(BaseModel):
    tracker_id: int
    tracker_name: str
    color: str
    seconds: float
