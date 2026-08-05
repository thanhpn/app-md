"""Generic adapter framework — adding a new site should mean adding a
Source row (config JSON), not writing a new Python class, for the two
generic adapters (`generic_html_product`, `generic_article`). A brand-new
adapter class is only needed for a fundamentally different fetch mechanism
(e.g. `youtube_channel`, which uses an API instead of scraping HTML).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FetchedPage:
    """1 URL's raw content, before parsing — this is what gets stored in
    RawItem.raw_content so a parse bug can be fixed and replayed without
    re-fetching."""

    url: str
    content: str


@dataclass
class ParsedProduct:
    url: str
    name: str
    external_id: str | None = None
    brand: str | None = None
    price: float | None = None
    currency: str = "VND"
    in_stock: bool | None = None
    images: list[str] = field(default_factory=list)
    specs: dict[str, Any] = field(default_factory=dict)
    category_path: str | None = None
    # The trackable/commission-earning link, when different from `url` (the
    # canonical product page used as identity/dedupe key) — e.g. Shopee's
    # affiliate `offerLink` vs its plain `productLink`. push_service uses
    # this for Offer.affiliate_url when present, falling back to `url`.
    affiliate_url: str | None = None


@dataclass
class ParsedContent:
    external_ref: str
    content_type: str  # one of app.models.CONTENT_TYPES
    body: str
    title: str | None = None
    author: str | None = None
    rating: float | None = None
    published_at: str | None = None  # ISO 8601, parsed by the caller


@dataclass
class AdapterResult:
    pages: list[FetchedPage]
    products: list[ParsedProduct] = field(default_factory=list)
    contents: list[ParsedContent] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class Adapter(ABC):
    """One adapter = one fetch+parse strategy. `config` is Source.config,
    validated/interpreted however the adapter needs (see each subclass's
    module docstring for the expected shape).
    """

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    async def run(self) -> AdapterResult: ...


_REGISTRY: dict[str, type[Adapter]] = {}


def register(key: str):
    def _wrap(cls: type[Adapter]) -> type[Adapter]:
        _REGISTRY[key] = cls
        return cls

    return _wrap


def get_adapter(key: str, config: dict) -> Adapter:
    if key not in _REGISTRY:
        raise ValueError(f"Unknown adapter_key '{key}' — registered: {sorted(_REGISTRY)}")
    return _REGISTRY[key](config)
