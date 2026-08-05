from app.services.dedupe import classify_raw_item, run_status


def test_classify_raw_item_new():
    assert classify_raw_item(None, "abc") == "new"


def test_classify_raw_item_unchanged():
    assert classify_raw_item("abc", "abc") == "unchanged"


def test_classify_raw_item_updated():
    assert classify_raw_item("abc", "xyz") == "updated"


def test_run_status_success_no_errors():
    assert run_status(errors_count=0, items_processed=5) == "success"


def test_run_status_success_when_nothing_found():
    assert run_status(errors_count=0, items_processed=0) == "success"


def test_run_status_failed_when_nothing_processed_but_items_existed():
    assert run_status(errors_count=3, items_processed=0) == "failed"


def test_run_status_failed_when_nothing_found_at_all():
    assert run_status(errors_count=1, items_processed=0) == "failed"


def test_run_status_partial_when_some_processed_despite_errors():
    assert run_status(errors_count=1, items_processed=4) == "partial"
