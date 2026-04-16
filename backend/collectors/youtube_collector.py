from __future__ import annotations

import logging
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Optional
from urllib.parse import urlparse

import httpx
import xml.etree.ElementTree as ET

from .base import BaseCollector, CollectedItem
from config import GroupConfig

logger = logging.getLogger(__name__)

YT_RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
ATOM_NS = "http://www.w3.org/2005/Atom"
MEDIA_NS = "http://search.yahoo.com/mrss/"
YT_NS = "http://www.youtube.com/xml/schemas/2015"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; idol-news-bot/1.0)",
}


def _parse_yt_rss(xml_text: str, group_slug: str) -> list[CollectedItem]:
    items: list[CollectedItem] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.warning("YouTube RSS parse error: %s", e)
        return items

    channel_name = root.findtext(f"{{{ATOM_NS}}}title") or "YouTube"

    for entry in root.findall(f"{{{ATOM_NS}}}entry"):
        video_id_elem = entry.find(f"{{{YT_NS}}}videoId")
        video_id = video_id_elem.text if video_id_elem is not None else None
        if not video_id:
            continue

        title_elem = entry.find(f"{{{ATOM_NS}}}title")
        title = (title_elem.text or "").strip() if title_elem is not None else ""
        if not title:
            continue

        published_str = entry.findtext(f"{{{ATOM_NS}}}published") or ""
        published_at: Optional[datetime] = None
        if published_str:
            try:
                published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00")).replace(tzinfo=None)
            except Exception:
                pass

        # media:group/media:thumbnail
        media_group = entry.find(f"{{{MEDIA_NS}}}group")
        thumbnail = None
        description = None
        if media_group is not None:
            thumb_elem = media_group.find(f"{{{MEDIA_NS}}}thumbnail")
            if thumb_elem is not None:
                thumbnail = thumb_elem.get("url")
            desc_elem = media_group.find(f"{{{MEDIA_NS}}}description")
            if desc_elem is not None:
                description = (desc_elem.text or "").strip()[:500] or None

        url = entry.findtext(f"{{{ATOM_NS}}}link[@rel='alternate']") or ""
        if not url:
            link_elem = entry.find(f"{{{ATOM_NS}}}link")
            url = link_elem.get("href", "") if link_elem is not None else ""
        if not url:
            url = f"https://www.youtube.com/watch?v={video_id}"

        items.append(
            CollectedItem(
                title=title,
                url=url,
                source_type="youtube",
                source_name=channel_name,
                group_slug=group_slug,
                published_at=published_at,
                thumbnail_url=thumbnail,
                summary=description,
                raw_metadata={"video_id": video_id},
            )
        )
    return items


class YouTubeCollector(BaseCollector):
    def __init__(self, group: GroupConfig, max_items: int = 30):
        super().__init__(group.slug, max_items)
        self.group = group

    async def collect(self) -> list[CollectedItem]:
        if not self.group.youtube_channel_ids:
            return []

        items: list[CollectedItem] = []
        async with httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True) as client:
            for channel_id in self.group.youtube_channel_ids:
                try:
                    url = YT_RSS_URL.format(channel_id=channel_id)
                    resp = await client.get(url)
                    resp.raise_for_status()
                    fetched = _parse_yt_rss(resp.text, self.group_slug)
                    items.extend(fetched)
                    logger.info("YouTube RSS %s: %d items", channel_id, len(fetched))
                except Exception as e:
                    logger.warning("YouTube RSS error for %s: %s", channel_id, e)

        return items[: self.max_items]
