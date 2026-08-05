import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SourceIn(BaseModel):
    name: str
    slug: str
    source_type: str
    adapter_key: str
    base_url: str
    config: dict = {}
    schedule_cron: str | None = None
    status: str = "active"


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    source_type: str
    adapter_key: str
    base_url: str
    config: dict
    schedule_cron: str | None
    status: str
    last_run_at: datetime | None
    reviews_category_id: str | None
    reviews_retailer_id: str | None
    created_at: datetime
    updated_at: datetime


class CrawlRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_id: uuid.UUID
    status: str
    started_at: datetime
    finished_at: datetime | None
    items_found: int
    items_new: int
    items_updated: int
    errors_count: int
    error_summary: str | None


class CrawledProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_id: uuid.UUID
    external_id: str | None
    url: str
    name: str
    brand: str | None
    price: float | None
    currency: str
    in_stock: bool | None
    images: list
    specs: dict
    category_path: str | None
    canonical_product_id: uuid.UUID | None
    first_seen_at: datetime
    last_seen_at: datetime


class CrawledContentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_id: uuid.UUID
    content_type: str
    external_ref: str
    title: str | None
    author: str | None
    rating: float | None
    body: str
    published_at: datetime | None
    related_product_id: uuid.UUID | None
    fetched_at: datetime


class Envelope(BaseModel):
    success: bool = True
    data: object = None
    error: dict | None = None
