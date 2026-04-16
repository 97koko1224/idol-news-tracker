from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from collectors.base import CollectedItem
from collectors.rss_collector import RssCollector
from collectors.youtube_collector import YouTubeCollector
from collectors.twitter_collector import TwitterCollector
from collectors.web_scraper import WebScraper
from config import get_config, GroupConfig, MemberConfig
from database import CollectionRun, Group, Member, NewsItem, SessionLocal

logger = logging.getLogger(__name__)


def _url_hash(url: str) -> str:
    return hashlib.sha256(url.strip().lower().encode()).hexdigest()


def _detect_member_tags(text: str, members: list[MemberConfig]) -> str:
    """テキスト中に登場するメンバーを検出してカンマ区切りで返す。
    漢字名・読み・ニックネームのいずれかが含まれていればタグ付けする。"""
    found = []
    for member in members:
        matched = False
        # 名前（漢字）が含まれていれば確定
        if member.name in text:
            matched = True
        # 読み・ニックネームでも判定（2文字以上のキーワードのみ）
        if not matched:
            for kw in member.keywords:
                if len(kw) >= 2 and kw in text:
                    matched = True
                    break
        if matched:
            found.append(member.name)
    return ",".join(found)


def sync_groups_from_config(db: Session) -> None:
    """config.yaml のグループ・メンバーを DB に同期する"""
    config = get_config()
    for group_cfg in config.groups:
        existing = db.query(Group).filter_by(slug=group_cfg.slug).first()
        if existing:
            existing.name = group_cfg.name
            group = existing
        else:
            group = Group(slug=group_cfg.slug, name=group_cfg.name)
            db.add(group)
            db.flush()

        # メンバー同期
        existing_members = {m.name: m for m in group.members}
        for member_cfg in group_cfg.members:
            if member_cfg.name in existing_members:
                m = existing_members[member_cfg.name]
                m.keywords_json = json.dumps(member_cfg.keywords, ensure_ascii=False)
                m.twitter_account = member_cfg.twitter_account
            else:
                db.add(
                    Member(
                        group_id=group.id,
                        name=member_cfg.name,
                        keywords_json=json.dumps(member_cfg.keywords, ensure_ascii=False),
                        twitter_account=member_cfg.twitter_account,
                    )
                )
    db.commit()


async def collect_group(group_cfg: GroupConfig, max_items: int) -> list[CollectedItem]:
    """1グループの全ソースから並列収集"""
    collectors = [
        RssCollector(group_cfg, max_items),
        YouTubeCollector(group_cfg, max_items),
        TwitterCollector(group_cfg, max_items),
        WebScraper(group_cfg, max_items),
    ]
    results = await asyncio.gather(
        *[c.collect() for c in collectors], return_exceptions=True
    )
    items: list[CollectedItem] = []
    for result in results:
        if isinstance(result, Exception):
            logger.warning("Collector error for %s: %s", group_cfg.name, result)
        else:
            items.extend(result)
    return items


async def run_collection() -> int:
    """全グループの収集を実行し、新規件数を返す"""
    config = get_config()
    db: Session = SessionLocal()

    run = CollectionRun(started_at=datetime.utcnow(), status="running")
    db.add(run)
    db.commit()
    db.refresh(run)
    run_id = run.id

    total_new = 0
    errors = []

    try:
        group_map: dict[str, tuple[int, list[MemberConfig]]] = {
            g.slug: (g.id, config.groups[i].members)
            for i, g in enumerate(db.query(Group).all())
            if i < len(config.groups)
        }
        # slug → (group_id, members)
        cfg_by_slug = {g.slug: g for g in config.groups}
        db_groups = {g.slug: g.id for g in db.query(Group).all()}

        tasks = [
            collect_group(g, config.settings.max_items_per_source)
            for g in config.groups
        ]
        all_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 今回のバッチ内での重複を防ぐセット
        seen_hashes: set[str] = set()

        for group_cfg, result in zip(config.groups, all_results):
            if isinstance(result, Exception):
                errors.append(f"{group_cfg.name}: {result}")
                continue

            group_id = db_groups.get(group_cfg.slug)
            if group_id is None:
                continue

            for item in result:
                url_hash = _url_hash(item.url)

                # バッチ内重複チェック
                if url_hash in seen_hashes:
                    continue
                seen_hashes.add(url_hash)

                # DB重複チェック
                if db.query(NewsItem).filter_by(url_hash=url_hash).first():
                    continue

                # メンバータグ検出（タイトル・サマリー・URLを対象）
                combined_text = item.title + " " + (item.summary or "") + " " + item.url
                member_tags = _detect_member_tags(combined_text, group_cfg.members)

                db.add(
                    NewsItem(
                        group_id=group_id,
                        source_type=item.source_type,
                        source_name=item.source_name,
                        title=item.title,
                        url=item.url,
                        url_hash=url_hash,
                        thumbnail_url=item.thumbnail_url,
                        summary=item.summary,
                        published_at=item.published_at,
                        member_tags=member_tags or None,
                        raw_metadata=json.dumps(item.raw_metadata, ensure_ascii=False)
                        if item.raw_metadata
                        else None,
                    )
                )
                total_new += 1

        db.commit()
        _cleanup_old_items(db, config.settings.retention_days)

        run_obj = db.query(CollectionRun).filter_by(id=run_id).first()
        run_obj.status = "completed"
        run_obj.finished_at = datetime.utcnow()
        run_obj.items_collected = total_new
        if errors:
            run_obj.error_message = json.dumps(errors, ensure_ascii=False)
        db.commit()

        logger.info("Collection completed: %d new items", total_new)

    except Exception as e:
        logger.exception("Collection failed")
        run_obj = db.query(CollectionRun).filter_by(id=run_id).first()
        if run_obj:
            run_obj.status = "failed"
            run_obj.finished_at = datetime.utcnow()
            run_obj.error_message = str(e)
            db.commit()
    finally:
        db.close()

    return total_new


def _cleanup_old_items(db: Session, retention_days: int) -> None:
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=retention_days)
    deleted = db.query(NewsItem).filter(NewsItem.published_at < cutoff).delete()
    db.commit()
    if deleted:
        logger.info("Cleaned up %d old items", deleted)
