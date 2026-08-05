from app.services.slugify import slugify


def test_slugify_vietnamese_diacritics():
    assert slugify("Điều hòa General 36000 BTU") == "dieu-hoa-general-36000-btu"


def test_slugify_plain_ascii():
    assert slugify("Hitachi HES-45VY") == "hitachi-hes-45vy"


def test_slugify_collapses_punctuation():
    assert slugify("A/B  &  C!!") == "a-b-c"


def test_slugify_empty_falls_back():
    assert slugify("") == "item"


def test_slugify_only_symbols_falls_back():
    assert slugify("---") == "item"
