import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.ai_parser import parse_invoice, normalize_category


def test_normalize_category_valid():
    assert normalize_category("餐飲") == "餐飲"
    assert normalize_category("交通") == "交通"


def test_normalize_category_unknown():
    assert normalize_category("未知分類") == "其他"
    assert normalize_category("") == "其他"
    assert normalize_category(None) == "其他"


@pytest.mark.asyncio
async def test_parse_invoice_success():
    mock_response = MagicMock()
    mock_response.text = '{"invoice_number": "AB-12345678", "store_name": "全聯", "date": "2026-01-15", "total_amount": 350, "items": [{"name": "牛奶", "price": 65, "quantity": 1}], "category": "日用品", "raw_text": "全聯 牛奶 65"}'

    mock_client = MagicMock()
    mock_model = MagicMock()
    mock_model.generate_content = MagicMock(return_value=mock_response)
    mock_client.models = mock_model

    with patch("app.services.ai_parser.genai.Client", return_value=mock_client):
        result = await parse_invoice(b"fake_image_bytes")

    assert result["store_name"] == "全聯"
    assert result["total_amount"] == 350
    assert len(result["items"]) == 1


@pytest.mark.asyncio
async def test_parse_invoice_unknown_category_normalized():
    mock_response = MagicMock()
    mock_response.text = '{"invoice_number": null, "store_name": "某店", "date": "2026-01-15", "total_amount": 100, "items": [{"name": "東西", "price": 100, "quantity": 1}], "category": "奇怪分類", "raw_text": ""}'

    mock_client = MagicMock()
    mock_model = MagicMock()
    mock_model.generate_content = MagicMock(return_value=mock_response)
    mock_client.models = mock_model

    with patch("app.services.ai_parser.genai.Client", return_value=mock_client):
        result = await parse_invoice(b"fake_image_bytes")

    assert result["category"] == "其他"


@pytest.mark.asyncio
async def test_parse_invoice_retry_on_429():
    from google.genai import errors as genai_errors

    error_response = MagicMock()
    error_response.status_code = 429
    error_response.headers = {}

    mock_response = MagicMock()
    mock_response.text = '{"invoice_number": null, "store_name": "店", "date": "2026-01-15", "total_amount": 50, "items": [{"name": "品項", "price": 50, "quantity": 1}], "category": "餐飲", "raw_text": ""}'

    mock_client = MagicMock()
    mock_model = MagicMock()
    mock_model.generate_content = MagicMock(
        side_effect=[
            genai_errors.ClientError(429, {"error": "rate limited"}, response=error_response),
            mock_response,
        ]
    )
    mock_client.models = mock_model

    with patch("app.services.ai_parser.genai.Client", return_value=mock_client):
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await parse_invoice(b"fake_image_bytes")

    assert result["store_name"] == "店"
