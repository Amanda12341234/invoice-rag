from datetime import date

from app.core.constants import VALID_CATEGORIES


def validate_invoice(data: dict) -> list[str]:
    errors = []
    if data.get("total_amount") is not None and data["total_amount"] < 0:
        errors.append("金額不可為負數")
    if data.get("date"):
        invoice_date = data["date"]
        if isinstance(invoice_date, str):
            invoice_date = date.fromisoformat(invoice_date)
        if invoice_date > date.today():
            errors.append("日期不可為未來日期")
    if not data.get("store_name"):
        errors.append("店名不可為空")
    if not data.get("items"):
        errors.append("至少需要一個品項")
    if data.get("category") and data["category"] not in VALID_CATEGORIES:
        errors.append(f"無效分類：{data['category']}")
    return errors
