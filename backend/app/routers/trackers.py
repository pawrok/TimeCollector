from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List

from ..database import get_session
from .. import crud
from ..models import Tracker
from ..schemas import TrackerCreate, TrackerUpdate, TrackerRead

router = APIRouter(prefix="/trackers", tags=["trackers"])


def build_read(db: Session, tracker: Tracker) -> TrackerRead:
    running = crud.get_running_session(db, tracker.id)
    return TrackerRead(
        id=tracker.id,
        name=tracker.name,
        color=tracker.color,
        sort_order=tracker.sort_order,
        archived=tracker.archived,
        created_at=tracker.created_at,
        is_running=running is not None,
        running_since=running.start_time if running else None,
        today_completed_seconds=crud.get_today_completed_seconds(db, tracker.id),
        total_seconds=crud.get_total_seconds(db, tracker.id),
    )


@router.post("/stop-all", status_code=204)
def stop_all(db: Session = Depends(get_session)):
    crud.stop_all_sessions(db)


@router.get("", response_model=List[TrackerRead])
def list_trackers(db: Session = Depends(get_session)):
    return [build_read(db, t) for t in crud.get_trackers(db)]


@router.post("", response_model=TrackerRead, status_code=201)
def create_tracker(data: TrackerCreate, db: Session = Depends(get_session)):
    return build_read(db, crud.create_tracker(db, data))


@router.patch("/{tracker_id}", response_model=TrackerRead)
def update_tracker(
    tracker_id: int, data: TrackerUpdate, db: Session = Depends(get_session)
):
    if not crud.get_tracker(db, tracker_id):
        raise HTTPException(404)
    return build_read(db, crud.update_tracker(db, tracker_id, data))


@router.delete("/{tracker_id}", status_code=204)
def delete_tracker(tracker_id: int, db: Session = Depends(get_session)):
    if not crud.get_tracker(db, tracker_id):
        raise HTTPException(404)
    crud.delete_tracker(db, tracker_id)


@router.post("/{tracker_id}/start", response_model=TrackerRead)
def start_tracker(tracker_id: int, db: Session = Depends(get_session)):
    tracker = crud.get_tracker(db, tracker_id)
    if not tracker:
        raise HTTPException(404)
    crud.start_session(db, tracker_id)
    return build_read(db, tracker)


@router.post("/{tracker_id}/stop", response_model=TrackerRead)
def stop_tracker(tracker_id: int, db: Session = Depends(get_session)):
    tracker = crud.get_tracker(db, tracker_id)
    if not tracker:
        raise HTTPException(404)
    crud.stop_tracker_sessions(db, tracker_id)
    return build_read(db, tracker)
