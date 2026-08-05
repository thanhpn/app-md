"""Pure classification helpers used by crawl_service — split out so they're
testable without a database."""


def classify_raw_item(previous_hash: str | None, new_hash: str) -> str:
    """RawItem.status for a (source, url) that was just re-fetched."""
    if previous_hash is None:
        return "new"
    if previous_hash == new_hash:
        return "unchanged"
    return "updated"


def run_status(errors_count: int, items_processed: int) -> str:
    """CrawlRun.status from the tallies of a finished run — a run with any
    error and 0 successfully processed items is a full failure regardless
    of how many items were *found* (e.g. yt-dlp listed 0 videos)."""
    if errors_count == 0:
        return "success"
    if items_processed == 0:
        return "failed"
    return "partial"
