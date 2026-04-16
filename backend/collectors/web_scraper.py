from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from .base import BaseCollector, CollectedItem
from config import GroupConfig, OfficialSite

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
}

DATE_PATTERN = re.compile(r"(\d{4})[./-年](\d{1,2})[./-月](\d{1,2})")


def _extract_date_from_text(text: str) -> Optional[datetime]:
    m = DATE_PATTERN.search(text)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    return None


def _normalize_url(url: str, base_url: str) -> str:
    if url.startswith("http"):
        return url
    return urljoin(base_url, url)


def _site_name(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return "official"


class GenericNewsListScraper:
    """汎用ニュースリストスクレイパー。
    ページ内のリンクと日付テキストを組み合わせてニュース記事を抽出する。
    """

    def scrape(self, html: str, base_url: str, group_slug: str) -> list[CollectedItem]:
        soup = BeautifulSoup(html, "lxml")
        items = []
        seen_urls: set[str] = set()

        # ニュースリストによく使われるセレクタを試行
        selectors = [
            "article", ".news-item", ".news_item", ".news-list li",
            ".newsList li", "ul.news li", ".topics-list li",
        ]

        candidates = []
        for sel in selectors:
            found = soup.select(sel)
            if found:
                candidates = found
                break

        # セレクタで見つからない場合はリンクから推定
        if not candidates:
            candidates = soup.find_all("a", href=True)

        for elem in candidates:
            # リンクを探す
            a_tag = elem if elem.name == "a" else elem.find("a", href=True)
            if not a_tag:
                continue

            href = a_tag.get("href", "")
            if not href or href == "#":
                continue

            url = _normalize_url(href, base_url)
            if url in seen_urls:
                continue
            seen_urls.add(url)

            # タイトル取得
            title = a_tag.get_text(strip=True)
            if not title:
                h = elem.find(re.compile(r"h[1-6]"))
                title = h.get_text(strip=True) if h else ""
            if not title or len(title) < 5:
                continue

            # 日付取得
            elem_text = elem.get_text(" ", strip=True)
            published_at = _extract_date_from_text(elem_text)

            # 日付がない、またはノイズが多いリンクを除外
            if not published_at and elem.name == "a":
                continue

            # 画像サムネイル
            img = elem.find("img")
            thumbnail = img.get("src") if img else None
            if thumbnail:
                thumbnail = _normalize_url(thumbnail, base_url)

            items.append(
                CollectedItem(
                    title=title[:200],
                    url=url,
                    source_type="web",
                    source_name=_site_name(base_url),
                    group_slug=group_slug,
                    published_at=published_at,
                    thumbnail_url=thumbnail,
                    summary=None,
                    raw_metadata={"scraped_from": base_url},
                )
            )

        return items[:30]


class AsobisystemScraper:
    """asobisystem.com グループ公式サイト専用スクレイパー。
    ul.list--information > li を対象にニュースを抽出する。
    """

    def scrape(self, html: str, base_url: str, group_slug: str) -> list[CollectedItem]:
        soup = BeautifulSoup(html, "lxml")
        items = []
        seen_urls: set[str] = set()

        ul = soup.select_one("ul.list--information")
        if not ul:
            logger.warning("asobisystem: ul.list--information not found at %s", base_url)
            return items

        for li in ul.find_all("li"):
            a_tag = li.find("a", href=True)
            if not a_tag:
                continue
            href = a_tag.get("href", "")
            url = _normalize_url(href, base_url)
            if url in seen_urls:
                continue
            seen_urls.add(url)

            title = a_tag.get_text(strip=True)
            # 日付プレフィックスを除去 (例: "2026.04.10タイトル" → "タイトル")
            title = DATE_PATTERN.sub("", title).strip()
            if not title or len(title) < 5:
                full_text = li.get_text(" ", strip=True)
                title = DATE_PATTERN.sub("", full_text).strip() or full_text
            if not title:
                continue

            elem_text = li.get_text(" ", strip=True)
            published_at = _extract_date_from_text(elem_text)

            img = li.find("img")
            thumbnail = None
            if img:
                src = img.get("src") or img.get("data-src", "")
                if src:
                    thumbnail = _normalize_url(src, base_url)

            items.append(
                CollectedItem(
                    title=title[:200],
                    url=url,
                    source_type="web",
                    source_name=_site_name(base_url),
                    group_slug=group_slug,
                    published_at=published_at,
                    thumbnail_url=thumbnail,
                    summary=None,
                    raw_metadata={"scraped_from": base_url},
                )
            )

        return items[:30]


SCRAPERS = {
    "generic_news_list": GenericNewsListScraper,
    "asobisystem": AsobisystemScraper,
}


class WebScraper(BaseCollector):
    def __init__(self, group: GroupConfig, max_items: int = 30):
        super().__init__(group.slug, max_items)
        self.group = group

    async def collect(self) -> list[CollectedItem]:
        if not self.group.official_sites:
            return []

        items: list[CollectedItem] = []
        async with httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True) as client:
            tasks = [self._scrape_site(client, site) for site in self.group.official_sites]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.warning("Web scrape error: %s", result)
                else:
                    items.extend(result)
        return items[: self.max_items]

    async def _scrape_site(self, client: httpx.AsyncClient, site: OfficialSite) -> list[CollectedItem]:
        await asyncio.sleep(1)  # 礼儀正しいクロール
        try:
            resp = await client.get(site.url)
            resp.raise_for_status()
        except Exception as e:
            logger.warning("Failed to scrape %s: %s", site.url, e)
            return []

        scraper_cls = SCRAPERS.get(site.scraper, GenericNewsListScraper)
        scraper = scraper_cls()
        return scraper.scrape(resp.text, site.url, self.group_slug)
