from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from sqlmodel import Session

from ..database import get_session
from .. import crud
from ..schemas import DailyStat, TotalStat

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/daily", response_model=List[DailyStat])
def daily_stats(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    db: Session = Depends(get_session),
):
    rows = crud.get_daily_stats(db, from_date, to_date)
    return [
        DailyStat(date=r[0], tracker_id=r[1], tracker_name=r[2], color=r[3], seconds=r[4])
        for r in rows
    ]


@router.get("/totals", response_model=List[TotalStat])
def total_stats(db: Session = Depends(get_session)):
    rows = crud.get_total_stats(db)
    return [
        TotalStat(tracker_id=r[0], tracker_name=r[1], color=r[2], seconds=r[3])
        for r in rows
    ]
