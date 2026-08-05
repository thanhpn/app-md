import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_basic_auth
from app.db import get_session
from app.models import CrawledContent, CrawledProduct
from app.schemas import CrawledContentOut, CrawledProductOut

router = APIRouter(prefix="/api/v1", tags=["items"], dependencies=[Depends(require_basic_auth)])


@router.get("/products", response_model=list[CrawledProductOut])
async def list_products(
    source_id: uuid.UUID | None = None,
    limit: int = Query(50, le=200),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(CrawledProduct).order_by(CrawledProduct.last_seen_at.desc()).limit(limit)
    if source_id is not None:
        stmt = stmt.where(CrawledProduct.source_id == source_id)
    rows = await session.execute(stmt)
    return list(rows.scalars())


@router.get("/content", response_model=list[CrawledContentOut])
async def list_content(
    source_id: uuid.UUID | None = None,
    limit: int = Query(50, le=200),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(CrawledContent).order_by(CrawledContent.fetched_at.desc()).limit(limit)
    if source_id is not None:
        stmt = stmt.where(CrawledContent.source_id == source_id)
    rows = await session.execute(stmt)
    return list(rows.scalars())
