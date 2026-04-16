from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

_default_db = Path(__file__).parent / "data" / "idol_news.db"
DB_PATH = Path(os.environ.get("DB_PATH", str(_default_db)))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
    echo=False,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String(100), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    news_items = relationship("NewsItem", back_populates="group", lazy="dynamic")
    members = relationship("Member", back_populates="group", lazy="select")


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    name = Column(String(100), nullable=False)
    keywords_json = Column(Text)   # JSON array
    twitter_account = Column(String(100))

    group = relationship("Group", back_populates="members")

    __table_args__ = (
        Index("idx_member_group_id", "group_id"),
    )


class NewsItem(Base):
    __tablename__ = "news_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    source_type = Column(String(20), nullable=False)  # rss | youtube | twitter | web
    source_name = Column(String(100), nullable=False)
    title = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    url_hash = Column(String(64), unique=True, nullable=False)
    thumbnail_url = Column(Text)
    summary = Column(Text)
    published_at = Column(DateTime)
    collected_at = Column(DateTime, server_default=func.now())
    raw_metadata = Column(Text)  # JSON
    # メンバー名タグ (カンマ区切り, タイトル/本文からマッチしたメンバー名)
    member_tags = Column(Text)

    group = relationship("Group", back_populates="news_items")

    __table_args__ = (
        Index("idx_news_group_id", "group_id"),
        Index("idx_news_published_at", "published_at"),
        Index("idx_news_source_type", "source_type"),
        Index("idx_news_collected_at", "collected_at"),
    )


class CollectionRun(Base):
    __tablename__ = "collection_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime)
    status = Column(String(20), nullable=False)  # running | completed | failed
    items_collected = Column(Integer, default=0)
    error_message = Column(Text)


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
