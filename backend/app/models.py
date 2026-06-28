from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship


class Tracker(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    color: str = Field(default="#6EA1F0")
    sort_order: int = Field(default=0)
    archived: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)

    sessions: List["TimerSession"] = Relationship(back_populates="tracker")


class TimerSession(SQLModel, table=True):
    __tablename__ = "session"
    id: Optional[int] = Field(default=None, primary_key=True)
    tracker_id: int = Field(foreign_key="tracker.id")
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = Field(default=None)

    tracker: Optional[Tracker] = Relationship(back_populates="sessions")
