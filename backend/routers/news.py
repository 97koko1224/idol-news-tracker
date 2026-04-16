from __future__ import annotations

import json
import math
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from database import Group, NewsItem, get_db

router = APIRouter(prefix="/api/news", tags=["news"])


class NewsItemOut(BaseModel):
    id: int
    group_id: int
    group_slug: str
    group_name: str
    source_type: str
    source_name: str
    title: str
    url: str
    thumbnail_url: Optional[str]
    summary: Optional[str]
    published_at: Optional[datetime]
    collected_at: Optional[datetime]
    member_tags: Optional[list[str]]

    model_config = {"from_attributes": True}


class NewsList(BaseModel):
    items: list[NewsItemOut]
    total: int
    page: int
    pages: int


def _build_item_out(item: NewsItem, group: Group) -> NewsItemOut:
    tags = None
    if item.member_tags:
        tags = [t for t in item.member_tags.split(",") if t]
    return NewsItemOut(
        id=item.id,
        group_id=item.group_id,
        group_slug=group.slug,
        group_name=group.name,
        source_type=item.source_type,
        source_name=item.source_name,
        title=item.title,
        url=item.url,
        thumbnail_url=item.thumbnail_url,
        summary=item.summary,
        published_at=item.published_at,
        collected_at=item.collected_at,
        member_tags=tags,
    )


@router.get("", response_model=NewsList)
def list_news(
    group_slug: Optional[str] = Query(None),
    source_type: Optional[str] = Query(None),
    member_name: Optional[str] = Query(None, description="メンバー名でフィルター"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(NewsItem, Group).join(Group, NewsItem.group_id == Group.id)

    if group_slug:
        group = db.query(Group).filter_by(slug=group_slug).first()
        if not group:
            raise HTTPException(404, "Group not found")
        q = q.filter(NewsItem.group_id == group.id)

    if source_type:
        q = q.filter(NewsItem.source_type == source_type)

    if member_name:
        # member_tags にメンバー名が含まれるもののみ表示
        q = q.filter(NewsItem.member_tags.contains(member_name))

    if date_from:
        q = q.filter(NewsItem.collected_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        q = q.filter(NewsItem.collected_at <= datetime.combine(date_to, datetime.max.time()))

    total = q.count()
    pages = max(1, math.ceil(total / per_page))

    rows = (
        q.order_by(
            func.coalesce(NewsItem.published_at, NewsItem.collected_at).desc()
        )
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    items = [_build_item_out(item, group) for item, group in rows]
    return NewsList(items=items, total=total, page=page, pages=pages)


@router.get("/{item_id}")
def get_news_item(item_id: int, db: Session = Depends(get_db)):
    row = db.query(NewsItem, Group).join(Group).filter(NewsItem.id == item_id).first()
    if not row:
        raise HTTPException(404, "Not found")
    item, group = row
    result = _build_item_out(item, group).model_dump()
    if item.raw_metadata:
        try:
            result["raw_metadata"] = json.loads(item.raw_metadata)
        except Exception:
            result["raw_metadata"] = {}
    return result
