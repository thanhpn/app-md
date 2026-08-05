import hashlib

from app.adapters.shopee_affiliate import parse_products, sign_request


def test_sign_request_matches_documented_formula():
    # sig = sha256(app_id + timestamp + payload + secret)
    expected = hashlib.sha256(b"app1" + b"1700000000" + b'{"a":1}' + b"secret1").hexdigest()
    assert sign_request("app1", "secret1", 1700000000, '{"a":1}') == expected


def test_sign_request_deterministic():
    a = sign_request("app", "secret", 123, "payload")
    b = sign_request("app", "secret", 123, "payload")
    assert a == b


def test_sign_request_sensitive_to_payload():
    a = sign_request("app", "secret", 123, "payload1")
    b = sign_request("app", "secret", 123, "payload2")
    assert a != b


def test_parse_products_maps_core_fields():
    nodes = [
        {
            "itemId": 111,
            "productName": "Điều hòa Test 9000 BTU",
            "productLink": "https://shopee.vn/product/1/111",
            "offerLink": "https://shope.ee/abc123",
            "imageUrl": "https://cf.shopee.vn/file/img1",
            "priceMin": "6990000",
            "priceMax": "6990000",
            "shopName": "Shop Điện Máy ABC",
            "ratingStar": "4.8",
            "commissionRate": "0.05",
        }
    ]
    products = parse_products(nodes)
    assert len(products) == 1
    p = products[0]
    assert p.name == "Điều hòa Test 9000 BTU"
    assert p.url == "https://shopee.vn/product/1/111"
    assert p.affiliate_url == "https://shope.ee/abc123"
    assert p.price == 6990000.0
    assert p.external_id == "111"
    assert p.images == ["https://cf.shopee.vn/file/img1"]
    assert p.specs == {"Cửa hàng": "Shop Điện Máy ABC", "Đánh giá": "4.8"}


def test_parse_products_skips_node_without_name_or_link():
    nodes = [{"itemId": 1, "productName": None, "productLink": "https://x"}, {"itemId": 2, "productName": "X"}]
    assert parse_products(nodes) == []


def test_parse_products_handles_missing_optional_fields():
    nodes = [{"itemId": 1, "productName": "Minimal", "productLink": "https://x"}]
    products = parse_products(nodes)
    assert len(products) == 1
    assert products[0].price is None
    assert products[0].images == []
    assert products[0].specs == {}
    assert products[0].affiliate_url is None


def test_parse_products_handles_unparseable_price():
    nodes = [{"itemId": 1, "productName": "X", "productLink": "https://x", "priceMin": "Liên hệ"}]
    assert parse_products(nodes)[0].price is None
