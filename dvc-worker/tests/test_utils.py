from app.adapters.utils import content_hash, filter_urls_by_pattern, parse_price, parse_selector, resolve_url


def test_parse_price_vnd_thousands_separator():
    assert parse_price("18.000.000 đ") == 18_000_000
    assert parse_price("1.299.000") == 1_299_000


def test_parse_price_comma_thousands_separator():
    assert parse_price("18,000,000 VND") == 18_000_000


def test_parse_price_decimal_usd():
    assert parse_price("USD 1,299.99") == 1299.99


def test_parse_price_plain_integer():
    assert parse_price("500000") == 500_000


def test_parse_price_none_when_no_digits():
    assert parse_price("Liên hệ") is None
    assert parse_price(None) is None
    assert parse_price("") is None


def test_parse_price_single_number_no_separator():
    assert parse_price("99") == 99


def test_content_hash_stable_and_sensitive():
    a = content_hash("hello world")
    b = content_hash("hello world")
    c = content_hash("hello world!")
    assert a == b
    assert a != c
    assert len(a) == 64


def test_resolve_url_relative():
    assert resolve_url("https://site.com/category/phones", "/p/123") == "https://site.com/p/123"


def test_resolve_url_absolute_passthrough():
    assert resolve_url("https://site.com/category/phones", "https://other.com/x") == "https://other.com/x"


def test_parse_selector_plain():
    assert parse_selector(".price") == (".price", None)


def test_parse_selector_with_attr():
    assert parse_selector("img.gallery::attr(src)") == ("img.gallery", "src")


def test_filter_urls_by_pattern_none_is_noop():
    urls = ["https://a.com/x", "https://a.com/y"]
    assert filter_urls_by_pattern(urls, None) == urls


def test_filter_urls_by_pattern_keeps_matching_only():
    urls = ["https://a.com/so-sanh.htm", "https://a.com/direct.htm?adsid=1"]
    assert filter_urls_by_pattern(urls, "so-sanh\\.htm") == ["https://a.com/so-sanh.htm"]


def test_filter_urls_by_pattern_empty_string_is_noop():
    urls = ["https://a.com/x"]
    assert filter_urls_by_pattern(urls, "") == urls
