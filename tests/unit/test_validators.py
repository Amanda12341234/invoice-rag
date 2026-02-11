from datetime import date, timedelta

from app.services.validators import validate_invoice


def test_valid_invoice():
    data = {
        "store_name": "全聯",
        "total_amount": 350,
        "date": date.today().isoformat(),
        "items": [{"name": "牛奶", "price": 65, "quantity": 1}],
        "category": "日用品",
    }
    assert validate_invoice(data) == []


def test_negative_amount():
    data = {
        "store_name": "店",
        "total_amount": -100,
        "date": date.today().isoformat(),
        "items": [{"name": "品項", "price": 50, "quantity": 1}],
        "category": "餐飲",
    }
    errors = validate_invoice(data)
    assert "金額不可為負數" in errors


def test_future_date():
    data = {
        "store_name": "店",
        "total_amount": 100,
        "date": (date.today() + timedelta(days=1)).isoformat(),
        "items": [{"name": "品項", "price": 50, "quantity": 1}],
        "category": "餐飲",
    }
    errors = validate_invoice(data)
    assert "日期不可為未來日期" in errors


def test_empty_store_name():
    data = {
        "store_name": "",
        "total_amount": 100,
        "date": date.today().isoformat(),
        "items": [{"name": "品項", "price": 50, "quantity": 1}],
        "category": "餐飲",
    }
    errors = validate_invoice(data)
    assert "店名不可為空" in errors


def test_no_items():
    data = {
        "store_name": "店",
        "total_amount": 100,
        "date": date.today().isoformat(),
        "items": [],
        "category": "餐飲",
    }
    errors = validate_invoice(data)
    assert "至少需要一個品項" in errors


def test_invalid_category():
    data = {
        "store_name": "店",
        "total_amount": 100,
        "date": date.today().isoformat(),
        "items": [{"name": "品項", "price": 50, "quantity": 1}],
        "category": "不存在的分類",
    }
    errors = validate_invoice(data)
    assert any("無效分類" in e for e in errors)
