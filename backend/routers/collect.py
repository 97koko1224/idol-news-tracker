from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import CollectionRun, get_db
from services.collection_service import run_collection

router = APIRouter(prefix="/api/collect", tags=["collect"])


class RunStatus(BaseModel):
    run_id: int
    status: str
    items_collected: Optional[int]
    error_message: Optional[str]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]


@router.post("")
async def trigger_collection(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_collection)
    return {"status": "started", "message": "収集を開始しました"}


@router.get("/history", response_model=list[RunStatus])
def collection_history(db: Session = Depends(get_db)):
    runs = (
        db.query(CollectionRun)
        .order_by(CollectionRun.started_at.desc())
        .limit(30)
        .all()
    )
    return [
        RunStatus(
            run_id=r.id,
            status=r.status,
            items_collected=r.items_collected,
            error_message=r.error_message,
            started_at=r.started_at,
            finished_at=r.finished_at,
        )
        for r in runs
    ]
