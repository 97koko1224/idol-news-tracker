from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import Group, NewsItem, get_db

router = APIRouter(prefix="/api/groups", tags=["groups"])


class GroupOut(BaseModel):
    id: int
    slug: str
    name: str
    item_count: int

    model_config = {"from_attributes": True}


class GroupDetail(GroupOut):
    stats_by_source: dict[str, int]


@router.get("", response_model=list[GroupOut])
def list_groups(db: Session = Depends(get_db)):
    rows = (
        db.query(Group, func.count(NewsItem.id).label("item_count"))
        .outerjoin(NewsItem, Group.id == NewsItem.group_id)
        .group_by(Group.id)
        .all()
    )
    return [
        GroupOut(id=g.id, slug=g.slug, name=g.name, item_count=cnt or 0)
        for g, cnt in rows
    ]


@router.get("/{slug}", response_model=GroupDetail)
def get_group(slug: str, db: Session = Depends(get_db)):
    group = db.query(Group).filter_by(slug=slug).first()
    if not group:
        raise HTTPException(404, "Group not found")

    stats = (
        db.query(NewsItem.source_type, func.count(NewsItem.id))
        .filter_by(group_id=group.id)
        .group_by(NewsItem.source_type)
        .all()
    )
    stats_by_source = {src: cnt for src, cnt in stats}
    total = sum(stats_by_source.values())

    return GroupDetail(
        id=group.id,
        slug=group.slug,
        name=group.name,
        item_count=total,
        stats_by_source=stats_by_source,
    )
