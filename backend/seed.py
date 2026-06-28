"""
Run from the backend/ directory:
    python seed.py

Inserts fake trackers and sessions into timecollector.db for chart testing.
Safe to run multiple times — skips creation if trackers already exist.
"""
import random
from datetime import datetime, timedelta, date

from sqlmodel import Session, select
from app.database import create_db_and_tables, engine
from app.models import Tracker, TimerSession

TRACKERS = [
    {"name": "Coding",    "color": "#6EA1F0"},
    {"name": "Reading",   "color": "#6EF09A"},
    {"name": "Meetings",  "color": "#F06E6E"},
    {"name": "Exercise",  "color": "#F0BD6E"},
]

random.seed(42)


def rand_sessions_for_day(tracker_name: str, day: date) -> list[tuple[datetime, datetime]]:
    """Return (start, end) pairs for a given tracker on a given day."""
    # Some trackers are busier than others; some days have no activity.
    weights = {
        "Coding":   0.85,
        "Reading":  0.60,
        "Meetings": 0.40,
        "Exercise": 0.70,
    }
    if random.random() > weights.get(tracker_name, 0.5):
        return []  # no activity this day

    # 1–3 sessions per active day
    n_sessions = random.choices([1, 2, 3], weights=[5, 3, 1])[0]
    sessions = []
    cursor_hour = random.uniform(8, 10)  # start somewhere in the morning

    for _ in range(n_sessions):
        # Duration: mostly 20 min – 2 h, occasionally longer
        duration_min = random.choices(
            [random.uniform(20, 60), random.uniform(60, 120), random.uniform(120, 240)],
            weights=[6, 3, 1],
        )[0]
        start = datetime(day.year, day.month, day.day) + timedelta(hours=cursor_hour)
        end = start + timedelta(minutes=duration_min)
        if end.date() > day:
            break
        sessions.append((start, end))
        cursor_hour += duration_min / 60 + random.uniform(0.5, 2)  # gap between sessions
        if cursor_hour > 22:
            break

    return sessions


def seed():
    create_db_and_tables()
    today = date.today()

    with Session(engine) as db:
        existing = db.exec(select(Tracker)).all()
        existing_names = {t.name for t in existing}

        trackers = []
        for i, td in enumerate(TRACKERS):
            if td["name"] in existing_names:
                print(f"  skip  {td['name']} (already exists)")
                t = db.exec(select(Tracker).where(Tracker.name == td["name"])).first()
            else:
                t = Tracker(name=td["name"], color=td["color"], sort_order=i)
                db.add(t)
                db.commit()
                db.refresh(t)
                print(f"  create {t.name}")
            trackers.append(t)

        total_sessions = 0
        for days_back in range(30, 0, -1):
            day = today - timedelta(days=days_back)
            for tracker in trackers:
                for start, end in rand_sessions_for_day(tracker.name, day):
                    db.add(TimerSession(tracker_id=tracker.id, start_time=start, end_time=end))
                    total_sessions += 1

        db.commit()
        print(f"\nDone — inserted {total_sessions} sessions across 30 days.")


if __name__ == "__main__":
    seed()
