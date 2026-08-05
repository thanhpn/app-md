import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_basic_auth
from app.db import get_session
from app.models import CrawlRun
from app.schemas import CrawlRunOut

router = APIRouter(prefix="/api/v1/runs", tags=["runs"], dependencies=[Depends(require_basic_auth)])


@router.get("", response_model=list[CrawlRunOut])
async def list_runs(
    source_id: uuid.UUID | None = None,
    limit: int = Query(50, le=200),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(CrawlRun).order_by(CrawlRun.started_at.desc()).limit(limit)
    if source_id is not None:
        stmt = stmt.where(CrawlRun.source_id == source_id)
    rows = await session.execute(stmt)
    return list(rows.scalars())
