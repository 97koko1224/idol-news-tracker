from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional
from urllib.parse import urlparse

import feedparser
import httpx

from .base import BaseCollector, CollectedItem
from config import GroupConfig

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
}


def _parse_date(entry: feedparser.FeedParserDict) -> Optional[datetime]:
    for attr in ("published", "updated"):
        val = getattr(entry, attr, None)
        if val:
            try:
                return parsedate_to_datetime(val).astimezone(timezone.utc).replace(tzinfo=None)
            except Exception:
                pass
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        import calendar
        return datetime.utcfromtimestamp(calendar.timegm(entry.published_parsed))
    return None


def _get_thumbnail(entry: feedparser.FeedParserDict) -> Optional[str]:
    for media in getattr(entry, "media_thumbnail", []):
        url = media.get("url")
        if url:
            return url
    for media in getattr(entry, "media_content", []):
        url = media.get("url", "")
        if url and any(url.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp")):
            return url
    return None


def _matches_keywords(text: str, keywords: list[str]) -> bool:
    if not keywords:
        return True
    text_lower = text.lower()
    for kw in keywords:
        if kw.lower() in text_lower or kw in text:
            return True
    return False


def _domain_name(url: str) -> str:
    try:
        host = urlparse(url).netloc
        return host.replace("www.", "").split(".")[0]
    except Exception:
        return "rss"


class RssCollector(BaseCollector):
    def __init__(self, group: GroupConfig, max_items: int = 30):
        super().__init__(group.slug, max_items)
        self.group = group

    async def collect(self) -> list[CollectedItem]:
        items: list[CollectedItem] = []
        async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True) as client:
            tasks = [self._fetch_feed(client, feed) for feed in self.group.rss_feeds]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.warning("RSS fetch error: %s", result)
                else:
                    items.extend(result)
        return items[: self.max_items]

    async def _fetch_feed(self, client: httpx.AsyncClient, feed) -> list[CollectedItem]:
        try:
            resp = await client.get(feed.url)
            resp.raise_for_status()
        except Exception as e:
            logger.warning("Failed to fetch %s: %s", feed.url, e)
            return []

        parsed = feedparser.parse(resp.text)
        source_name = _domain_name(feed.url)
        items = []

        for entry in parsed.entries:
            title = getattr(entry, "title", "") or ""
            summary = getattr(entry, "summary", "") or ""
            url = getattr(entry, "link", "") or ""

            if not title or not url:
                continue

            combined_text = title + " " + summary
            if not _matches_keywords(combined_text, feed.filter_keywords):
                continue

            items.append(
                CollectedItem(
                    title=title.strip(),
                    url=url.strip(),
                    source_type="rss",
                    source_name=source_name,
                    group_slug=self.group_slug,
                    published_at=_parse_date(entry),
                    thumbnail_url=_get_thumbnail(entry),
                    summary=summary[:500] if summary else None,
                    raw_metadata={"feed_url": feed.url},
                )
            )

        return items
