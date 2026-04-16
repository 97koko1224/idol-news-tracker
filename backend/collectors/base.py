from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class CollectedItem:
    title: str
    url: str
    source_type: str      # rss | youtube | twitter | web
    source_name: str
    group_slug: str
    published_at: Optional[datetime] = None
    thumbnail_url: Optional[str] = None
    summary: Optional[str] = None
    raw_metadata: Optional[dict] = field(default=None)


class BaseCollector(ABC):
    def __init__(self, group_slug: str, max_items: int = 30):
        self.group_slug = group_slug
        self.max_items = max_items

    @abstractmethod
    async def collect(self) -> list[CollectedItem]:
        """収集を実行してCollectedItemリストを返す"""
        ...
