from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import Group, Member, get_db

router = APIRouter(prefix="/api/members", tags=["members"])


class MemberOut(BaseModel):
    id: int
    name: str
    group_slug: str
    group_name: str
    keywords: list[str]
    twitter_account: Optional[str]


@router.get("", response_model=list[MemberOut])
def list_members(group_slug: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Member, Group).join(Group, Member.group_id == Group.id)
    if group_slug:
        q = q.filter(Group.slug == group_slug)
    rows = q.order_by(Group.id, Member.id).all()

    result = []
    for member, group in rows:
        try:
            keywords = json.loads(member.keywords_json or "[]")
        except Exception:
            keywords = [member.name]
        result.append(
            MemberOut(
                id=member.id,
                name=member.name,
                group_slug=group.slug,
                group_name=group.name,
                keywords=keywords,
                twitter_account=member.twitter_account or None,
            )
        )
    return result
