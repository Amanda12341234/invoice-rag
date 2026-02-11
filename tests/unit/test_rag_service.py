import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from app.services.rag_service import (
    TOOL_DEFINITIONS,
    query_database,
    search_invoices,
    truncate_history,
)


def test_tool_definitions_exist():
    names = [t["name"] for t in TOOL_DEFINITIONS]
    assert "query_database" in names
    assert "search_invoices" in names
    assert "get_spending_summary" in names
    assert "get_category_breakdown" in names


def test_query_database(session_fixture):
    result = query_database(session_fixture, user_id=1, period="2026-01")
    assert "total" in result


def test_search_invoices():
    mock_vs = MagicMock()
    mock_vs.search.return_value = [
        {"document": "2026-01-15 在星巴克購買咖啡 $120 (餐飲)", "metadata": {"invoice_id": 1}}
    ]
    result = search_invoices(mock_vs, user_id=1, query="咖啡")
    assert len(result) == 1


def test_truncate_history():
    history = [{"role": "user", "content": f"msg{i}"} for i in range(10)]
    truncated = truncate_history(history, max_turns=5)
    assert len(truncated) == 10  # 5 turns = 10 messages (user + assistant)


def test_truncate_history_short():
    history = [{"role": "user", "content": "hi"}]
    truncated = truncate_history(history, max_turns=5)
    assert len(truncated) == 1


@pytest.fixture
def session_fixture():
    mock_session = MagicMock()
    mock_session.exec.return_value.all.return_value = []
    mock_session.exec.return_value.first.return_value = (0, 0.0)
    return mock_session
