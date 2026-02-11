import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient
from sqlmodel import Session

from app.auth import hash_password, create_access_token
from app.models.user import User


@pytest.mark.asyncio
async def test_chat_success(client: AsyncClient, auth_headers):
    with patch("app.api.v1.chat.handle_chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = {
            "answer": "您這個月共花費 1000 元",
            "sources": [],
        }
        response = await client.post(
            "/api/v1/chat",
            json={"message": "這個月花了多少？"},
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "1000" in data["answer"]


@pytest.mark.asyncio
async def test_chat_unauthorized(client: AsyncClient):
    response = await client.post(
        "/api/v1/chat",
        json={"message": "test"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_chat_user_isolation(client: AsyncClient, auth_headers, session: Session, test_user):
    with patch("app.api.v1.chat.handle_chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = {"answer": "回答", "sources": []}

        await client.post(
            "/api/v1/chat",
            json={"message": "查詢"},
            headers=auth_headers,
        )

        mock_chat.assert_called_once()
        kwargs = mock_chat.call_args.kwargs
        assert kwargs["user_id"] == test_user.id
