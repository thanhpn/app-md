import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_basic_auth
from app.db import get_session
from app.models import CrawlRun, Source
from app.scheduler import reload_jobs
from app.schemas import CrawlRunOut, SourceIn, SourceOut
from app.services.crawl_service import run_source

router = APIRouter(prefix="/api/v1/sources", tags=["sources"], dependencies=[Depends(require_basic_auth)])


@router.get("", response_model=list[SourceOut])
async def list_sources(session: AsyncSession = Depends(get_session)):
    rows = await session.execute(select(Source).order_by(Source.created_at.desc()))
    return list(rows.scalars())


@router.post("", response_model=SourceOut, status_code=201)
async def create_source(payload: SourceIn, session: AsyncSession = Depends(get_session)):
    source = Source(**payload.model_dump())
    session.add(source)
    await session.commit()
    await session.refresh(source)
    await reload_jobs()
    return source


@router.get("/{source_id}", response_model=SourceOut)
async def get_source(source_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    source = await session.get(Source, source_id)
    if source is None:
        raise HTTPException(404, "Source not found")
    return source


@router.put("/{source_id}", response_model=SourceOut)
async def update_source(source_id: uuid.UUID, payload: SourceIn, session: AsyncSession = Depends(get_session)):
    source = await session.get(Source, source_id)
    if source is None:
        raise HTTPException(404, "Source not found")
    for field, value in payload.model_dump().items():
        setattr(source, field, value)
    await session.commit()
    await session.refresh(source)
    await reload_jobs()
    return source


@router.delete("/{source_id}", status_code=204)
async def delete_source(source_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    source = await session.get(Source, source_id)
    if source is None:
        raise HTTPException(404, "Source not found")
    await session.delete(source)
    await session.commit()
    await reload_jobs()


@router.post("/{source_id}/run", response_model=CrawlRunOut)
async def trigger_run(source_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    source = await session.get(Source, source_id)
    if source is None:
        raise HTTPException(404, "Source not found")
    run: CrawlRun = await run_source(session, source)
    return run
