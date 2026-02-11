import pytest
from httpx import AsyncClient
from sqlmodel import Session

from app.auth import hash_password, create_access_token
from app.models.user import User


def make_invoice_data(invoice_number, date_str):
    return {
        "store_name": "全聯",
        "date": date_str,
        "total_amount": 100,
        "items": [{"name": "品項", "price": 100, "quantity": 1}],
        "category": "日用品",
        "invoice_number": invoice_number,
    }


@pytest.mark.asyncio
async def test_calendar_returns_daily_summary(client: AsyncClient, auth_headers):
    await client.post(
        "/api/v1/invoices", json=make_invoice_data("C1", "2026-01-10"), headers=auth_headers
    )
    await client.post(
        "/api/v1/invoices", json=make_invoice_data("C2", "2026-01-10"), headers=auth_headers
    )
    await client.post(
        "/api/v1/invoices", json=make_invoice_data("C3", "2026-01-15"), headers=auth_headers
    )

    response = await client.get(
        "/api/v1/invoices/calendar?year=2026&month=1", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    day10 = next(d for d in data if d["date"] == "2026-01-10")
    assert day10["count"] == 2
    assert day10["total_amount"] == 200.0


@pytest.mark.asyncio
async def test_calendar_user_isolation(client: AsyncClient, auth_headers, session: Session):
    await client.post(
        "/api/v1/invoices", json=make_invoice_data("C4", "2026-03-10"), headers=auth_headers
    )

    user_b = User(username="caluser", hashed_password=hash_password("password123"))
    session.add(user_b)
    session.commit()
    session.refresh(user_b)
    headers_b = {"Authorization": f"Bearer {create_access_token(user_b.id)}"}

    response = await client.get(
        "/api/v1/invoices/calendar?year=2026&month=3", headers=headers_b
    )
    assert response.status_code == 200
    assert len(response.json()) == 0


@pytest.mark.asyncio
async def test_calendar_empty_month(client: AsyncClient, auth_headers):
    response = await client.get(
        "/api/v1/invoices/calendar?year=2025&month=6", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json() == []
