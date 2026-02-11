import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={"username": "newuser", "password": "pass123456"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"username": "dupuser", "password": "pass123456"},
    )
    response = await client.post(
        "/api/v1/auth/register",
        json={"username": "dupuser", "password": "pass654321"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"username": "loginuser", "password": "pass123456"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "loginuser", "password": "pass123456"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"username": "wrongpw", "password": "pass123456"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "wrongpw", "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_without_token(client: AsyncClient):
    response = await client.get("/api/v1/invoices")
    assert response.status_code == 401
