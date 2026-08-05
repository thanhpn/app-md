import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import is_logged_in, log_in, log_out
from app.config import settings
from app.db import get_session
from app.models import CrawledContent, CrawledProduct, CrawlRun, Source
from app.scheduler import reload_jobs
from app.services.crawl_service import run_source
from app.services.push_service import push_source
from app.services.reviews_client import ReviewsClientError

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def _render(request: Request, template: str, **ctx):
    ctx.setdefault("request", request)
    ctx.setdefault("logged_in", is_logged_in(request))
    ctx.setdefault("flash", request.query_params.get("flash"))
    ctx.setdefault("flash_type", request.query_params.get("flash_type"))
    return templates.TemplateResponse(template, ctx)


def _require_login(request: Request) -> RedirectResponse | None:
    if not is_logged_in(request):
        return RedirectResponse("/admin/login", status_code=303)
    return None


@router.get("/")
async def index():
    return RedirectResponse("/admin/sources", status_code=303)


@router.get("/login")
async def login_form(request: Request):
    if is_logged_in(request):
        return RedirectResponse("/admin/sources", status_code=303)
    return _render(request, "login.html")


@router.post("/login")
async def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == settings.admin_username and password == settings.admin_password:
        log_in(request)
        return RedirectResponse("/admin/sources", status_code=303)
    return _render(request, "login.html", error="Sai tài khoản hoặc mật khẩu.")


@router.post("/logout")
async def logout(request: Request):
    log_out(request)
    return RedirectResponse("/admin/login", status_code=303)


@router.get("/sources")
async def sources_list(request: Request, session: AsyncSession = Depends(get_session)):
    if redirect := _require_login(request):
        return redirect
    rows = await session.execute(select(Source).order_by(Source.created_at.desc()))
    return _render(request, "sources_list.html", sources=list(rows.scalars()))


@router.get("/sources/new")
async def sources_new_form(request: Request):
    if redirect := _require_login(request):
        return redirect
    return _render(request, "source_form.html", source=None)


@router.post("/sources/new")
async def sources_new_submit(
    request: Request,
    name: str = Form(...),
    slug: str = Form(...),
    source_type: str = Form(...),
    adapter_key: str = Form(...),
    base_url: str = Form(...),
    config: str = Form("{}"),
    schedule_cron: str = Form(""),
    status: str = Form("active"),
    session: AsyncSession = Depends(get_session),
):
    if redirect := _require_login(request):
        return redirect
    form = {
        "name": name,
        "slug": slug,
        "source_type": source_type,
        "adapter_key": adapter_key,
        "base_url": base_url,
        "config": config,
        "schedule_cron": schedule_cron,
        "status": status,
    }
    try:
        config_dict = json.loads(config or "{}")
    except json.JSONDecodeError as exc:
        return _render(request, "source_form.html", source=None, form=form, error=f"Config không phải JSON hợp lệ: {exc}")

    source = Source(
        name=name,
        slug=slug,
        source_type=source_type,
        adapter_key=adapter_key,
        base_url=base_url,
        config=config_dict,
        schedule_cron=schedule_cron or None,
        status=status,
    )
    session.add(source)
    await session.commit()
    await reload_jobs()
    return RedirectResponse("/admin/sources?flash=" + f"Đã thêm nguồn {name}", status_code=303)


@router.get("/sources/{source_id}/edit")
async def sources_edit_form(request: Request, source_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    if redirect := _require_login(request):
        return redirect
    source = await session.get(Source, source_id)
    if source is None:
        return RedirectResponse("/admin/sources?flash=Không tìm thấy nguồn&flash_type=error", status_code=303)
    return _render(request, "source_form.html", source=source)


@router.post("/sources/{source_id}/edit")
async def sources_edit_submit(
    request: Request,
    source_id: uuid.UUID,
    name: str = Form(...),
    slug: str = Form(...),
    source_type: str = Form(...),
    adapter_key: str = Form(...),
    base_url: str = Form(...),
    config: str = Form("{}"),
    schedule_cron: str = Form(""),
    status: str = Form("active"),
    session: AsyncSession = Depends(get_session),
):
    if redirect := _require_login(request):
        return redirect
    source = await session.get(Source, source_id)
    if source is None:
        return RedirectResponse("/admin/sources?flash=Không tìm thấy nguồn&flash_type=error", status_code=303)

    form = {
        "name": name,
        "slug": slug,
        "source_type": source_type,
        "adapter_key": adapter_key,
        "base_url": base_url,
        "config": config,
        "schedule_cron": schedule_cron,
        "status": status,
    }
    try:
        config_dict = json.loads(config or "{}")
    except json.JSONDecodeError as exc:
        return _render(request, "source_form.html", source=source, form=form, error=f"Config không phải JSON hợp lệ: {exc}")

    source.name = name
    source.slug = slug
    source.source_type = source_type
    source.adapter_key = adapter_key
    source.base_url = base_url
    source.config = config_dict
    source.schedule_cron = schedule_cron or None
    source.status = status
    await session.commit()
    await reload_jobs()
    return RedirectResponse("/admin/sources?flash=" + f"Đã lưu {name}", status_code=303)


@router.post("/sources/{source_id}/delete")
async def sources_delete(request: Request, source_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    if redirect := _require_login(request):
        return redirect
    source = await session.get(Source, source_id)
    if source is not None:
        await session.delete(source)
        await session.commit()
        await reload_jobs()
    return RedirectResponse("/admin/sources?flash=Đã xoá nguồn", status_code=303)


@router.post("/sources/{source_id}/run")
async def sources_run(request: Request, source_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    if redirect := _require_login(request):
        return redirect
    source = await session.get(Source, source_id)
    if source is None:
        return RedirectResponse("/admin/sources?flash=Không tìm thấy nguồn&flash_type=error", status_code=303)
    run = await run_source(session, source)
    flash = f"Crawl xong: {run.status} — {run.items_new} mới, {run.items_updated} cập nhật, {run.errors_count} lỗi"
    flash_type = "error" if run.status == "failed" else None
    url = f"/admin/runs?source_id={source_id}&flash={flash}"
    if flash_type:
        url += f"&flash_type={flash_type}"
    return RedirectResponse(url, status_code=303)


@router.post("/sources/{source_id}/push")
async def sources_push(
    request: Request,
    source_id: uuid.UUID,
    category_name: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    if redirect := _require_login(request):
        return redirect
    source = await session.get(Source, source_id)
    if source is None:
        return RedirectResponse("/admin/sources?flash=Không tìm thấy nguồn&flash_type=error", status_code=303)
    try:
        result = await push_source(session, source, category_name)
    except ReviewsClientError as exc:
        return RedirectResponse(f"/admin/sources?flash=Đẩy dữ liệu thất bại: {exc}&flash_type=error", status_code=303)

    flash = f"Đã đẩy sang Review: {result.pushed_new} sản phẩm mới, {result.pushed_updated} cập nhật"
    flash_type = None
    if result.errors:
        flash += f", {len(result.errors)} lỗi ({'; '.join(result.errors[:3])})"
        flash_type = "error"
    url = f"/admin/products?source_id={source_id}&flash={flash}"
    if flash_type:
        url += f"&flash_type={flash_type}"
    return RedirectResponse(url, status_code=303)


@router.get("/runs")
async def runs_list(request: Request, source_id: uuid.UUID | None = None, session: AsyncSession = Depends(get_session)):
    if redirect := _require_login(request):
        return redirect
    stmt = select(CrawlRun).order_by(CrawlRun.started_at.desc()).limit(100)
    if source_id is not None:
        stmt = stmt.where(CrawlRun.source_id == source_id)
    rows = await session.execute(stmt)
    runs = list(rows.scalars())

    sources_rows = await session.execute(select(Source))
    sources_by_id = {s.id: s.name for s in sources_rows.scalars()}
    source = await session.get(Source, source_id) if source_id else None

    return _render(request, "runs_list.html", runs=runs, sources_by_id=sources_by_id, source=source)


@router.get("/products")
async def products_list(request: Request, source_id: uuid.UUID | None = None, session: AsyncSession = Depends(get_session)):
    if redirect := _require_login(request):
        return redirect
    stmt = select(CrawledProduct).order_by(CrawledProduct.last_seen_at.desc()).limit(200)
    if source_id is not None:
        stmt = stmt.where(CrawledProduct.source_id == source_id)
    rows = await session.execute(stmt)
    products = list(rows.scalars())

    sources_rows = await session.execute(select(Source))
    sources_by_id = {s.id: s.name for s in sources_rows.scalars()}
    source = await session.get(Source, source_id) if source_id else None

    return _render(request, "products_list.html", products=products, sources_by_id=sources_by_id, source=source)


@router.get("/content")
async def content_list(request: Request, source_id: uuid.UUID | None = None, session: AsyncSession = Depends(get_session)):
    if redirect := _require_login(request):
        return redirect
    stmt = select(CrawledContent).order_by(CrawledContent.fetched_at.desc()).limit(200)
    if source_id is not None:
        stmt = stmt.where(CrawledContent.source_id == source_id)
    rows = await session.execute(stmt)
    items = list(rows.scalars())

    sources_rows = await session.execute(select(Source))
    sources_by_id = {s.id: s.name for s in sources_rows.scalars()}
    source = await session.get(Source, source_id) if source_id else None

    return _render(request, "content_list.html", items=items, sources_by_id=sources_by_id, source=source)
