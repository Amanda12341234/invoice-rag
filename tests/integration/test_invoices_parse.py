import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_parse_invoice_success(client: AsyncClient, auth_headers):
    mock_response = MagicMock()
    mock_response.text = '{"invoice_number": "AB-12345678", "store_name": "全聯", "date": "2026-01-15", "total_amount": 350, "items": [{"name": "牛奶", "price": 65, "quantity": 1}], "category": "日用品", "raw_text": "全聯 牛奶 65"}'

    mock_client = MagicMock()
    mock_model = MagicMock()
    mock_model.generate_content = MagicMock(return_value=mock_response)
    mock_client.models = mock_model

    with patch("app.services.ai_parser.genai.Client", return_value=mock_client):
        response = await client.post(
            "/api/v1/invoices/parse",
            headers=auth_headers,
            files={"file": ("invoice.jpg", b"fake_image_bytes", "image/jpeg")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["store_name"] == "全聯"
    assert data["total_amount"] == 350


@pytest.mark.asyncio
async def test_parse_invoice_unauthorized(client: AsyncClient):
    response = await client.post(
        "/api/v1/invoices/parse",
        files={"file": ("invoice.jpg", b"fake_image_bytes", "image/jpeg")},
    )
    assert response.status_code == 401
