import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session

from app.auth import hash_password
from app.models.user import User

scenarios("../features/auth.feature")


@pytest.fixture
def context():
    return {}


@given(parsers.parse('一個新使用者 "{username}" 密碼 "{password}"'))
def new_user(context, username, password):
    context["username"] = username
    context["password"] = password


@given(parsers.parse('已存在使用者 "{username}" 密碼 "{password}"'))
@pytest.mark.asyncio
async def existing_user(context, username, password, client, session):
    user = User(username=username, hashed_password=hash_password(password))
    session.add(user)
    session.commit()
    context["username"] = username
    context["password"] = password


@when("使用者送出註冊請求")
@pytest.mark.asyncio
async def send_register(context, client):
    response = await client.post(
        "/api/v1/auth/register",
        json={"username": context["username"], "password": context["password"]},
    )
    context["response"] = response


@when(parsers.parse('使用者以 "{username}" 密碼 "{password}" 送出註冊請求'))
@pytest.mark.asyncio
async def send_register_with(context, username, password, client):
    response = await client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": password},
    )
    context["response"] = response


@when(parsers.parse('使用者以 "{username}" 密碼 "{password}" 送出登入請求'))
@pytest.mark.asyncio
async def send_login(context, username, password, client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    context["response"] = response


@when("使用者未帶 token 存取受保護端點")
@pytest.mark.asyncio
async def access_without_token(context, client):
    response = await client.get("/api/v1/invoices")
    context["response"] = response


@then(parsers.parse("回應狀態碼為 {status_code:d}"))
def check_status(context, status_code):
    assert context["response"].status_code == status_code


@then(parsers.parse('回應包含使用者名稱 "{username}"'))
def check_username(context, username):
    assert context["response"].json()["username"] == username


@then("回應包含 access_token")
def check_access_token(context):
    assert "access_token" in context["response"].json()
