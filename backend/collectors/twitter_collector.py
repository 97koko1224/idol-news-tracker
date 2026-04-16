from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Optional

import httpx

from .base import BaseCollector, CollectedItem
from config import GroupConfig

logger = logging.getLogger(__name__)

SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"
TWEET_FIELDS = "created_at,author_id,entities,attachments"
EXPANSIONS = "author_id,attachments.media_keys"
MEDIA_FIELDS = "preview_image_url,url,type"
USER_FIELDS = "name,username"


def _parse_twitter_date(date_str: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


class TwitterCollector(BaseCollector):
    def __init__(self, group: GroupConfig, max_items: int = 30):
        super().__init__(group.slug, max_items)
        self.group = group
        self.bearer_token = os.environ.get("TWITTER_BEARER_TOKEN", "")

    async def collect(self) -> list[CollectedItem]:
        if not self.bearer_token:
            logger.info("TWITTER_BEARER_TOKEN not set, skipping Twitter for %s", self.group.name)
            return []

        # アカウント検索 + グループキーワード検索の両方を実行
        queries = self._build_queries()
        if not queries:
            return []

        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        items: list[CollectedItem] = []
        seen_ids: set[str] = set()

        async with httpx.AsyncClient(headers=headers, timeout=15) as client:
            tasks = [self._search(client, q) for q in queries]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.warning("Twitter API error for %s: %s", self.group.name, result)
                    continue
                for item in result:
                    tweet_id = (item.raw_metadata or {}).get("tweet_id", "")
                    if tweet_id and tweet_id not in seen_ids:
                        seen_ids.add(tweet_id)
                        items.append(item)

        # 日付降順でソート
        items.sort(key=lambda x: x.published_at or datetime.min, reverse=True)
        return items[: self.max_items]

    def _build_queries(self) -> list[str]:
        """検索クエリを組み立てる。アカウント指定 + グループキーワード。"""
        queries = []

        # 公式アカウントのツイート
        for account in self.group.twitter_accounts:
            q = f"from:{account} -is:retweet lang:ja"
            queries.append(q)

        # グループ名でのキーワード検索（アカウントがない場合 or 補完）
        if self.group.keywords:
            kw = self.group.keywords[0]  # 英語グループ名（例: FRUITS ZIPPER）
            q = f'"{kw}" -is:retweet lang:ja'
            queries.append(q)

        return queries[:3]  # 月500件制限を考慮して最大3クエリ

    async def _search(self, client: httpx.AsyncClient, query: str) -> list[CollectedItem]:
        params = {
            "query": query,
            "max_results": min(self.max_items, 10),  # Free tier: max 10
            "tweet.fields": TWEET_FIELDS,
            "expansions": EXPANSIONS,
            "media.fields": MEDIA_FIELDS,
            "user.fields": USER_FIELDS,
        }
        try:
            resp = await client.get(SEARCH_URL, params=params)
            if resp.status_code == 429:
                logger.warning("Twitter API rate limit hit for %s", self.group.name)
                return []
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.warning("Twitter API HTTP error: %s %s", e.response.status_code, e.response.text[:200])
            return []

        data = resp.json()
        tweets = data.get("data", [])
        includes = data.get("includes", {})

        # ユーザー情報マップ
        users = {u["id"]: u for u in includes.get("users", [])}
        # メディアマップ
        media_map = {m["media_key"]: m for m in includes.get("media", [])}

        items = []
        for tweet in tweets:
            tweet_id = tweet.get("id", "")
            text = tweet.get("text", "").strip()
            if not text or not tweet_id:
                continue

            author_id = tweet.get("author_id", "")
            user = users.get(author_id, {})
            username = user.get("username", "unknown")
            display_name = user.get("name", username)

            published_at = _parse_twitter_date(tweet.get("created_at", ""))

            # サムネイル取得
            thumbnail = None
            attachments = tweet.get("attachments", {})
            media_keys = attachments.get("media_keys", [])
            for mk in media_keys:
                m = media_map.get(mk, {})
                thumb = m.get("preview_image_url") or m.get("url")
                if thumb:
                    thumbnail = thumb
                    break

            # ツイートURLはx.comで統一
            url = f"https://x.com/{username}/status/{tweet_id}"

            items.append(
                CollectedItem(
                    title=text[:200],
                    url=url,
                    source_type="twitter",
                    source_name=f"@{username}",
                    group_slug=self.group_slug,
                    published_at=published_at,
                    thumbnail_url=thumbnail,
                    summary=None,
                    raw_metadata={"tweet_id": tweet_id, "username": username},
                )
            )
        return items
