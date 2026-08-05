import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.requests import Request

from app.config import settings

_basic = HTTPBasic()


def require_basic_auth(credentials: HTTPBasicCredentials = Depends(_basic)) -> str:
    """Guards the JSON API (/api/v1/*) — meant for scripts/future services,
    not the browser admin UI (which uses the session cookie instead)."""
    valid_user = secrets.compare_digest(credentials.username, settings.admin_username)
    valid_pass = secrets.compare_digest(credentials.password, settings.admin_password)
    if not (valid_user and valid_pass):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials", headers={"WWW-Authenticate": "Basic"})
    return credentials.username


def is_logged_in(request: Request) -> bool:
    return request.session.get("authenticated") is True


def log_in(request: Request) -> None:
    request.session["authenticated"] = True


def log_out(request: Request) -> None:
    request.session.clear()
