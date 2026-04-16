from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from config import get_config
from database import create_tables, SessionLocal
from services.collection_service import run_collection, sync_groups_from_config
from routers import groups, news, collect, stats, members

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

scheduler: AsyncIOScheduler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler

    create_tables()
    with SessionLocal() as db:
        sync_groups_from_config(db)

    config = get_config()
    hour, minute = config.settings.collect_time.split(":")
    scheduler = AsyncIOScheduler(timezone=config.settings.timezone)
    scheduler.add_job(
        func=run_collection,
        trigger=CronTrigger(hour=int(hour), minute=int(minute)),
        id="daily_collection",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    logger.info(
        "Scheduler started. Daily collection at %s (%s)",
        config.settings.collect_time,
        config.settings.timezone,
    )

    yield

    if scheduler:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title="Idol News Tracker API",
    description="KAWAII LAB. 最新情報収集プラットフォーム",
    version="1.0.0",
    lifespan=lifespan,
)

_origins_env = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000")
_allowed_origins = [o.strip() for o in _origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(groups.router)
app.include_router(members.router)
app.include_router(news.router)
app.include_router(collect.router)
app.include_router(stats.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
