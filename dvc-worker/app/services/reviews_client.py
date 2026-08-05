"""Thin client for dvc-api/apps/reviews' admin API — how push_service.py
gets crawled data into reviews-web. Auth: logs in once as a dedicated admin
account (see README "Đẩy dữ liệu sang reviews-web"), caches the access
token in memory, re-logs in on 401 (no refresh-token rotation — this
process runs rarely enough that a fresh login each expiry is simpler than
tracking refresh state).
"""

import asyncio
import re

import httpx

from app.config import settings

_IAM_LOGIN_PATH_RE = re.compile(r"/api/v1/reviews/?$")


class ReviewsClientError(Exception):
    pass


class ReviewsClient:
    def __init__(self):
        if not settings.reviews_api_base_url:
            raise ReviewsClientError("REVIEWS_API_BASE_URL not configured — see .env.example")
        self._base_url = settings.reviews_api_base_url.rstrip("/")
        # Admin login lives at the IAM root (…/api/v1/admin/auth/login), not
        # under the reviews app's own path — derive it by stripping the
        # reviews-specific suffix off the configured base URL.
        self._iam_base_url = _IAM_LOGIN_PATH_RE.sub("", self._base_url) or self._base_url
        self._token: str | None = None

    async def _login(self, client: httpx.AsyncClient) -> None:
        resp = await client.post(
            f"{self._iam_base_url}/api/v1/admin/auth/login",
            headers={"X-App-Key": settings.reviews_app_key},
            json={"email": settings.reviews_admin_email, "password": settings.reviews_admin_password},
        )
        if resp.status_code != 200:
            raise ReviewsClientError(f"reviews admin login failed: {resp.status_code} {resp.text}")
        data = resp.json()["data"]
        self._token = data["access_token"]

    async def _request(self, client: httpx.AsyncClient, method: str, path: str, **kwargs) -> dict:
        if self._token is None:
            await self._login(client)

        resp = await client.request(method, f"{self._base_url}{path}", headers={"Authorization": f"Bearer {self._token}"}, **kwargs)
        if resp.status_code == 401:
            await self._login(client)
            resp = await client.request(method, f"{self._base_url}{path}", headers={"Authorization": f"Bearer {self._token}"}, **kwargs)

        # The gateway's per-IP rate limiter (see docs/services/gateway.md) can
        # trip during a large push even with push_service's pacing — a couple
        # of short backoff retries clears it without surfacing a spurious
        # per-item failure for what's really just "wait a second and retry".
        retry_delay = 1.5
        for _ in range(3):
            if resp.status_code != 429:
                break
            await asyncio.sleep(retry_delay)
            retry_delay *= 2
            resp = await client.request(method, f"{self._base_url}{path}", headers={"Authorization": f"Bearer {self._token}"}, **kwargs)

        if resp.status_code >= 400:
            raise ReviewsClientError(f"{method} {path} -> {resp.status_code}: {resp.text[:500]}")
        if resp.status_code == 204:
            return {}
        envelope = resp.json()
        if not envelope.get("success", True):
            raise ReviewsClientError(f"{method} {path} -> {envelope.get('error')}")
        return envelope.get("data", envelope)

    async def get_or_create_category(self, client: httpx.AsyncClient, name: str, slug: str) -> str:
        categories = await self._request(client, "GET", "/admin/categories")
        for cat in categories:
            if cat["slug"] == slug:
                return cat["id"]
        created = await self._request(client, "POST", "/admin/categories", json={"name": name, "slug": slug, "sort_order": 0})
        return created["id"]

    async def get_or_create_retailer(self, client: httpx.AsyncClient, name: str, slug: str, website_url: str | None) -> str:
        retailers = await self._request(client, "GET", "/admin/retailers")
        for r in retailers:
            if r["slug"] == slug:
                return r["id"]
        created = await self._request(
            client, "POST", "/admin/retailers", json={"name": name, "slug": slug, "website_url": website_url}
        )
        return created["id"]

    async def create_product(self, client: httpx.AsyncClient, payload: dict) -> str:
        created = await self._request(client, "POST", "/admin/products", json=payload)
        return created["id"]

    async def update_product(self, client: httpx.AsyncClient, product_id: str, payload: dict) -> None:
        await self._request(client, "PATCH", f"/admin/products/{product_id}", json=payload)

    async def set_product_status(self, client: httpx.AsyncClient, product_id: str, status: str) -> None:
        await self._request(client, "PATCH", f"/admin/products/{product_id}/status", json={"status": status})

    async def list_offers(self, client: httpx.AsyncClient, product_id: str) -> list[dict]:
        return await self._request(client, "GET", "/admin/offers", params={"product_id": product_id})

    async def create_offer(self, client: httpx.AsyncClient, payload: dict) -> str:
        created = await self._request(client, "POST", "/admin/offers", json=payload)
        return created["id"]

    async def update_offer(self, client: httpx.AsyncClient, offer_id: str, payload: dict) -> None:
        await self._request(client, "PATCH", f"/admin/offers/{offer_id}", json=payload)
