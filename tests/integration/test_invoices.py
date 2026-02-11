import pytest
from httpx import AsyncClient
from sqlmodel import Session

from app.auth import hash_password, create_access_token
from app.models.user import User


def make_invoice_data(**overrides):
    data = {
        "store_name": "全聯",
        "date": "2026-01-15",
        "total_amount": 350,
        "items": [{"name": "牛奶", "price": 65, "quantity": 1}],
        "category": "日用品",
        "invoice_number": "AB-12345678",
    }
    data.update(overrides)
    return data


@pytest.mark.asyncio
async def test_create_invoice(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/v1/invoices", json=make_invoice_data(), headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["store_name"] == "全聯"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_create_invoice_duplicate(client: AsyncClient, auth_headers):
    await client.post(
        "/api/v1/invoices", json=make_invoice_data(), headers=auth_headers
    )
    response = await client.post(
        "/api/v1/invoices", json=make_invoice_data(), headers=auth_headers
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_invoice_duplicate_force_save(client: AsyncClient, auth_headers):
    await client.post(
        "/api/v1/invoices", json=make_invoice_data(), headers=auth_headers
    )
    response = await client.post(
        "/api/v1/invoices",
        json=make_invoice_data(force_save=True, invoice_number="AB-12345679"),
        headers=auth_headers,
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_list_invoices_with_date_filter(client: AsyncClient, auth_headers):
    await client.post(
        "/api/v1/invoices",
        json=make_invoice_data(invoice_number="A1", date="2026-01-10"),
        headers=auth_headers,
    )
    await client.post(
        "/api/v1/invoices",
        json=make_invoice_data(invoice_number="A2", date="2026-02-15"),
        headers=auth_headers,
    )

    response = await client.get(
        "/api/v1/invoices?start_date=2026-01-01&end_date=2026-01-31",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["invoice_number"] == "A1"


@pytest.mark.asyncio
async def test_get_invoice_detail(client: AsyncClient, auth_headers):
    create_resp = await client.post(
        "/api/v1/invoices", json=make_invoice_data(), headers=auth_headers
    )
    invoice_id = create_resp.json()["id"]

    response = await client.get(
        f"/api/v1/invoices/{invoice_id}", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["store_name"] == "全聯"
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_get_invoice_not_found(client: AsyncClient, auth_headers):
    response = await client.get("/api/v1/invoices/99999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_invoice(client: AsyncClient, auth_headers):
    create_resp = await client.post(
        "/api/v1/invoices", json=make_invoice_data(), headers=auth_headers
    )
    invoice_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/v1/invoices/{invoice_id}",
        json={"store_name": "家樂福"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["store_name"] == "家樂福"


@pytest.mark.asyncio
async def test_delete_invoice(client: AsyncClient, auth_headers):
    create_resp = await client.post(
        "/api/v1/invoices", json=make_invoice_data(), headers=auth_headers
    )
    invoice_id = create_resp.json()["id"]

    response = await client.delete(
        f"/api/v1/invoices/{invoice_id}", headers=auth_headers
    )
    assert response.status_code == 204

    get_resp = await client.get(
        f"/api/v1/invoices/{invoice_id}", headers=auth_headers
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_user_isolation(client: AsyncClient, auth_headers, session: Session):
    # User A creates invoice
    await client.post(
        "/api/v1/invoices", json=make_invoice_data(), headers=auth_headers
    )

    # Create user B
    user_b = User(username="userb", hashed_password=hash_password("password123"))
    session.add(user_b)
    session.commit()
    session.refresh(user_b)
    token_b = create_access_token(user_b.id)
    headers_b = {"Authorization": f"Bearer {token_b}"}

    response = await client.get("/api/v1/invoices", headers=headers_b)
    assert response.status_code == 200
    assert len(response.json()) == 0
