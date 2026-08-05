import re
import unicodedata


def slugify(text: str) -> str:
    """ASCII-fold + lowercase + hyphenate — good enough for Vietnamese
    product/category/retailer names (đ isn't decomposed by NFKD, handled
    separately)."""
    text = text.replace("đ", "d").replace("Đ", "D")
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text).strip("-").lower()
    return slug or "item"
