from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import CollectionRun, Group, NewsItem, get_db

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("")
def get_stats(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)

    total = db.query(func.count(NewsItem.id)).scalar() or 0
    today_count = (
        db.query(func.count(NewsItem.id))
        .filter(NewsItem.collected_at >= today_start)
        .scalar()
        or 0
    )
    week_count = (
        db.query(func.count(NewsItem.id))
        .filter(NewsItem.collected_at >= week_start)
        .scalar()
        or 0
    )

    by_group = (
        db.query(Group.slug, Group.name, func.count(NewsItem.id).label("cnt"))
        .outerjoin(NewsItem, Group.id == NewsItem.group_id)
        .group_by(Group.id)
        .order_by(func.count(NewsItem.id).desc())
        .all()
    )

    by_source = (
        db.query(NewsItem.source_type, func.count(NewsItem.id))
        .group_by(NewsItem.source_type)
        .all()
    )

    last_run = (
        db.query(CollectionRun)
        .filter(CollectionRun.status == "completed")
        .order_by(CollectionRun.finished_at.desc())
        .first()
    )

    return {
        "total_items": total,
        "items_today": today_count,
        "items_this_week": week_count,
        "by_group": [{"slug": s, "name": n, "count": c} for s, n, c in by_group],
        "by_source": {src: cnt for src, cnt in by_source},
        "last_collected_at": last_run.finished_at.isoformat() if last_run else None,
    }
