import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app import adapters  # noqa: F401 — import registers all built-in adapters
from app.admin.routes import router as admin_router
from app.api.items import router as items_router
from app.api.runs import router as runs_router
from app.api.sources import router as sources_router
from app.config import settings
from app.scheduler import reload_jobs, scheduler

logging.basicConfig(level=settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    await reload_jobs()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="dvc-worker", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key)

app.mount("/admin/static", StaticFiles(directory=str(Path(__file__).parent / "admin" / "static")), name="admin-static")

app.include_router(sources_router)
app.include_router(runs_router)
app.include_router(items_router)
app.include_router(admin_router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
