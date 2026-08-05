"""Pure helper functions shared by adapters — kept dependency-free (no
network, no DB) so they're cheap to unit test directly."""

import hashlib
import re
from urllib.parse import urljoin

_DIGIT_GROUP_RE = re.compile(r"[\d.,]+")


def parse_price(text: str | None) -> float | None:
    """Extract a price from free-form text like '18.000.000 đ' or
    '1,299.99 USD' — assumes '.'/',' are thousands separators (true for
    VND-formatted prices, the common case here) unless the group ends in
    exactly 2 digits after the last separator, which is treated as a
    decimal (covers 'USD 1,299.99')."""
    if not text:
        return None
    match = _DIGIT_GROUP_RE.search(text)
    if not match:
        return None
    raw = match.group(0)
    last_sep = max(raw.rfind("."), raw.rfind(","))
    if last_sep != -1 and len(raw) - last_sep - 1 == 2:
        integer_part = re.sub(r"[.,]", "", raw[:last_sep])
        decimal_part = raw[last_sep + 1 :]
        cleaned = f"{integer_part}.{decimal_part}"
    else:
        cleaned = re.sub(r"[.,]", "", raw)
    try:
        return float(cleaned)
    except ValueError:
        return None


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def resolve_url(base_url: str, href: str) -> str:
    return urljoin(base_url, href)


def parse_selector(selector: str) -> tuple[str, str | None]:
    """'.price::attr(content)' -> ('.price', 'content'); '.price' -> ('.price', None)."""
    match = re.match(r"^(.*?)::attr\(([^)]+)\)$", selector.strip())
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return selector.strip(), None


def filter_urls_by_pattern(urls: list[str], pattern: str | None) -> list[str]:
    """Keep only URLs matching `pattern` (regex, re.search) — used to drop
    sponsored/ad links that share a listing page's link selector with real
    product links but point at a different URL shape (e.g. an affiliate
    redirect instead of the site's own product page). None/blank pattern is
    a no-op (keeps everything)."""
    if not pattern:
        return urls
    regex = re.compile(pattern)
    return [u for u in urls if regex.search(u)]
