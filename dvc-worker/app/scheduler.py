"""Cron-driven auto-crawling. Sources with schedule_cron set get a job;
sources with schedule_cron=None are manual-trigger-only. Call reload_jobs()
after any Source create/update/delete/status change so the schedule stays
in sync with the DB — this module is deliberately the only place that
knows how to turn Source rows into APScheduler jobs.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.db import SessionLocal
from app.models import Source
from app.services.crawl_service import run_source

logger = logging.getLogger("dvc_worker.scheduler")

scheduler = AsyncIOScheduler()


async def _run_job(source_id):
    async with SessionLocal() as session:
        source = await session.get(Source, source_id)
        if source is None or source.status != "active" or not source.schedule_cron:
            return
        try:
            await run_source(session, source)
        except Exception:
            logger.exception("scheduled run failed for source_id=%s", source_id)


async def reload_jobs() -> None:
    scheduler.remove_all_jobs()
    async with SessionLocal() as session:
        rows = await session.execute(select(Source).where(Source.status == "active", Source.schedule_cron.is_not(None)))
        sources = list(rows.scalars())

    for source in sources:
        try:
            trigger = CronTrigger.from_crontab(source.schedule_cron)
        except ValueError:
            logger.warning("source_id=%s has invalid schedule_cron=%r, skipping", source.id, source.schedule_cron)
            continue
        scheduler.add_job(_run_job, trigger=trigger, args=[source.id], id=str(source.id), replace_existing=True)
