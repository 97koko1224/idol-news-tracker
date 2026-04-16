from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

CONFIG_PATH = Path(__file__).parent / "config.yaml"


@dataclass
class RssFeed:
    url: str
    filter_keywords: list[str] = field(default_factory=list)


@dataclass
class OfficialSite:
    url: str
    scraper: str = "generic_news_list"


@dataclass
class MemberConfig:
    name: str
    reading: str = ""
    keywords: list[str] = field(default_factory=list)
    twitter_account: str = ""


@dataclass
class GroupConfig:
    name: str
    slug: str
    keywords: list[str] = field(default_factory=list)
    twitter_accounts: list[str] = field(default_factory=list)
    youtube_channel_ids: list[str] = field(default_factory=list)
    rss_feeds: list[RssFeed] = field(default_factory=list)
    official_sites: list[OfficialSite] = field(default_factory=list)
    members: list[MemberConfig] = field(default_factory=list)

    def all_keywords(self) -> list[str]:
        """グループ + 全メンバーのキーワード一覧"""
        kws = list(self.keywords)
        for m in self.members:
            kws.extend(m.keywords)
        return kws


@dataclass
class Settings:
    collect_time: str = "08:00"
    timezone: str = "Asia/Tokyo"
    max_items_per_source: int = 50
    retention_days: int = 90


@dataclass
class AppConfig:
    settings: Settings
    groups: list[GroupConfig]

    def all_members(self) -> list[tuple[str, MemberConfig]]:
        """(group_slug, member) のタプルリストを返す"""
        result = []
        for g in self.groups:
            for m in g.members:
                result.append((g.slug, m))
        return result


def load_config() -> AppConfig:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    settings_raw = raw.get("settings", {})
    settings = Settings(
        collect_time=settings_raw.get("collect_time", "08:00"),
        timezone=settings_raw.get("timezone", "Asia/Tokyo"),
        max_items_per_source=settings_raw.get("max_items_per_source", 50),
        retention_days=settings_raw.get("retention_days", 90),
    )

    groups = []
    for g in raw.get("groups", []):
        rss_feeds = [RssFeed(**f) for f in g.get("rss_feeds", [])]
        official_sites = [OfficialSite(**s) for s in g.get("official_sites", [])]
        members = []
        for m in g.get("members", []):
            members.append(
                MemberConfig(
                    name=m["name"],
                    reading=m.get("reading", ""),
                    keywords=m.get("keywords", [m["name"]]),
                    twitter_account=m.get("twitter_account", ""),
                )
            )
        groups.append(
            GroupConfig(
                name=g["name"],
                slug=g["slug"],
                keywords=g.get("keywords", []),
                twitter_accounts=g.get("twitter_accounts", []),
                youtube_channel_ids=g.get("youtube_channel_ids", []),
                rss_feeds=rss_feeds,
                official_sites=official_sites,
                members=members,
            )
        )

    return AppConfig(settings=settings, groups=groups)


_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config() -> AppConfig:
    global _config
    _config = load_config()
    return _config


def get_env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)
