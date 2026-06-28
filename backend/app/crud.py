from datetime import datetime, date, timezone
from typing import Optional
from sqlmodel import Session, select
from sqlalchemy import text
from .models import Tracker, TimerSession
from .schemas import TrackerCreate, TrackerUpdate

COLORS = [
    "#6EA1F0", "#F06E6E", "#6EF09A", "#F0BD6E",
    "#BD6EF0", "#6EE8F0", "#F06EBD", "#F0E96E",
]


def get_trackers(db: Session) -> list[Tracker]:
    return db.exec(
        select(Tracker)
        .where(Tracker.archived == False)
        .order_by(Tracker.sort_order, Tracker.id)
    ).all()


def get_tracker(db: Session, tracker_id: int) -> Optional[Tracker]:
    return db.get(Tracker, tracker_id)


def create_tracker(db: Session, data: TrackerCreate) -> Tracker:
    count = len(db.exec(select(Tracker)).all())
    tracker = Tracker(
        name=data.name,
        color=data.color or COLORS[count % len(COLORS)],
        sort_order=count,
    )
    db.add(tracker)
    db.commit()
    db.refresh(tracker)
    return tracker


def update_tracker(db: Session, tracker_id: int, data: TrackerUpdate) -> Tracker:
    tracker = db.get(Tracker, tracker_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(tracker, key, value)
    db.add(tracker)
    db.commit()
    db.refresh(tracker)
    return tracker


def delete_tracker(db: Session, tracker_id: int):
    stop_tracker_sessions(db, tracker_id)
    sessions = db.exec(
        select(TimerSession).where(TimerSession.tracker_id == tracker_id)
    ).all()
    for s in sessions:
        db.delete(s)
    tracker = db.get(Tracker, tracker_id)
    db.delete(tracker)
    db.commit()


def get_running_session(db: Session, tracker_id: int) -> Optional[TimerSession]:
    return db.exec(
        select(TimerSession)
        .where(TimerSession.tracker_id == tracker_id)
        .where(TimerSession.end_time == None)
    ).first()


def start_session(db: Session, tracker_id: int) -> TimerSession:
    stop_all_sessions(db)
    session = TimerSession(tracker_id=tracker_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def stop_tracker_sessions(db: Session, tracker_id: int):
    running = db.exec(
        select(TimerSession)
        .where(TimerSession.tracker_id == tracker_id)
        .where(TimerSession.end_time == None)
    ).all()
    for s in running:
        s.end_time = datetime.now(timezone.utc)
        db.add(s)
    db.commit()


def stop_all_sessions(db: Session, end_time: Optional[datetime] = None):
    t = end_time or datetime.now(timezone.utc)
    running = db.exec(
        select(TimerSession).where(TimerSession.end_time == None)
    ).all()
    for s in running:
        s.end_time = t
        db.add(s)
    db.commit()


def get_today_completed_seconds(db: Session, tracker_id: int) -> float:
    today = date.today().isoformat()
    row = db.execute(
        text("""
            SELECT COALESCE(SUM(
                (julianday(end_time) - julianday(start_time)) * 86400
            ), 0)
            FROM session
            WHERE tracker_id = :tid
              AND end_time IS NOT NULL
              AND date(start_time, 'localtime') = :today
        """),
        {"tid": tracker_id, "today": today},
    ).fetchone()
    return float(row[0]) if row else 0.0


def get_total_seconds(db: Session, tracker_id: int) -> float:
    row = db.execute(
        text("""
            SELECT COALESCE(SUM(
                (julianday(COALESCE(end_time, datetime('now')))
                 - julianday(start_time)) * 86400
            ), 0)
            FROM session
            WHERE tracker_id = :tid
        """),
        {"tid": tracker_id},
    ).fetchone()
    return float(row[0]) if row else 0.0


def get_daily_stats(
    db: Session,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> list:
    query = """
        SELECT
            date(s.start_time, 'localtime') as day,
            s.tracker_id,
            t.name as tracker_name,
            t.color,
            COALESCE(SUM(
                (julianday(COALESCE(s.end_time, datetime('now')))
                 - julianday(s.start_time)) * 86400
            ), 0) as seconds
        FROM session s
        JOIN tracker t ON t.id = s.tracker_id
        WHERE 1=1
    """
    params: dict = {}
    if from_date:
        query += " AND date(s.start_time, 'localtime') >= :from_date"
        params["from_date"] = from_date
    if to_date:
        query += " AND date(s.start_time, 'localtime') <= :to_date"
        params["to_date"] = to_date
    query += " GROUP BY day, s.tracker_id ORDER BY day, s.tracker_id"
    return db.execute(text(query), params).fetchall()


def get_total_stats(db: Session) -> list:
    return db.execute(
        text("""
            SELECT
                s.tracker_id,
                t.name as tracker_name,
                t.color,
                COALESCE(SUM(
                    (julianday(COALESCE(s.end_time, datetime('now')))
                     - julianday(s.start_time)) * 86400
                ), 0) as seconds
            FROM session s
            JOIN tracker t ON t.id = s.tracker_id
            GROUP BY s.tracker_id
            ORDER BY seconds DESC
        """)
    ).fetchall()
