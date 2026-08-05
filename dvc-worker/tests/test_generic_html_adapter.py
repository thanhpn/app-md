from app.adapters.generic_html_product import GenericHtmlProductAdapter

FIXTURE_HTML = """
<html><body>
  <h1 class="product-title">Điện thoại ABC Pro</h1>
  <span class="price">18.000.000 đ</span>
  <span class="brand">ABC</span>
  <span class="sku" data-sku="SKU-123">ignored text</span>
  <div class="breadcrumb">Trang chủ / Điện thoại</div>
  <div class="gallery">
    <img class="gallery-img" src="/img/1.jpg" />
    <img class="gallery-img" src="/img/2.jpg" />
  </div>
  <table class="specs-table">
    <tr><th>RAM</th><td>8GB</td></tr>
    <tr><th>Bộ nhớ</th><td>128GB</td></tr>
  </table>
</body></html>
"""

CONFIG = {
    "selectors": {
        "name": "h1.product-title",
        "price": ".price",
        "brand": ".brand",
        "external_id": ".sku::attr(data-sku)",
        "images": "img.gallery-img::attr(src)",
        "category_path": ".breadcrumb",
    },
    "specs_selector": ".specs-table tr",
}


def test_parse_product_extracts_all_fields():
    adapter = GenericHtmlProductAdapter(CONFIG)
    product = adapter._parse_product("https://shop.example.com/p/abc-pro", FIXTURE_HTML)

    assert product is not None
    assert product.name == "Điện thoại ABC Pro"
    assert product.price == 18_000_000
    assert product.brand == "ABC"
    assert product.external_id == "SKU-123"
    assert product.category_path == "Trang chủ / Điện thoại"
    assert product.images == [
        "https://shop.example.com/img/1.jpg",
        "https://shop.example.com/img/2.jpg",
    ]
    assert product.specs == {"RAM": "8GB", "Bộ nhớ": "128GB"}


def test_parse_product_returns_none_without_name():
    adapter = GenericHtmlProductAdapter({"selectors": {"name": ".missing"}})
    assert adapter._parse_product("https://shop.example.com/p/x", FIXTURE_HTML) is None


def test_parse_product_works_with_minimal_config():
    adapter = GenericHtmlProductAdapter({"selectors": {"name": "h1.product-title"}})
    product = adapter._parse_product("https://shop.example.com/p/x", FIXTURE_HTML)
    assert product is not None
    assert product.name == "Điện thoại ABC Pro"
    assert product.price is None
    assert product.images == []
    assert product.specs == {}
