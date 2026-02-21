import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Ensure backend is in path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.repositories.spanner_graph import SpannerSoulRepository
from app.models.graph import FactNode

@pytest.fixture
def mock_spanner():
    with patch("app.repositories.spanner_graph.spanner") as mock:
        mock.param_types.STRING = "STRING"
        mock.param_types.FLOAT64 = "FLOAT64"
        mock.param_types.INT64 = "INT64"
        mock.param_types.Array = MagicMock(return_value="ARRAY")
        yield mock

@pytest.fixture
def mock_embedding_service():
    with patch("app.repositories.spanner_graph.embedding_service") as mock:
        mock.embed_text = AsyncMock(return_value=[0.1, 0.2, 0.3])
        yield mock

@pytest.mark.asyncio
async def test_save_fact(mock_spanner, mock_embedding_service):
    repo = SpannerSoulRepository()
    # Mock the database connection
    repo.database = MagicMock()
    # Mock run_in_transaction to execute the callback and return a mock ID
    def side_effect(callback):
        # We don't execute the callback fully because it requires a transaction object
        # which acts on the database. We just want to ensure run_in_transaction is called.
        # But wait, save_fact defines save_tx and passes it.
        # We can just return the ID.
        return "fact-123"

    repo.database.run_in_transaction.side_effect = side_effect

    fact = await repo.save_fact("user-1", "content", "category")

    assert fact.id == "fact-123"
    assert fact.content == "content"
    assert fact.embedding == [0.1, 0.2, 0.3]

    # Verify embed_text called
    mock_embedding_service.embed_text.assert_called_once_with("content")

    # Verify transaction called
    repo.database.run_in_transaction.assert_called_once()

@pytest.mark.asyncio
async def test_get_relevant_facts(mock_spanner, mock_embedding_service):
    repo = SpannerSoulRepository()
    repo.database = MagicMock()
    mock_snapshot = MagicMock()
    repo.database.snapshot.return_value.__enter__.return_value = mock_snapshot

    # Mock results
    mock_snapshot.execute_sql.return_value = [
        ("fact-1", "content1", "cat1", 0.9),
        ("fact-2", "content2", "cat2", 0.8)
    ]

    facts = await repo.get_relevant_facts("user-1", "query")

    assert len(facts) == 2
    assert facts[0].id == "fact-1"
    assert facts[0].content == "content1"

    # Verify embed_text called
    mock_embedding_service.embed_text.assert_called_once_with("query")

    # Verify SQL executed with correct params
    mock_snapshot.execute_sql.assert_called_once()
    call_args = mock_snapshot.execute_sql.call_args
    gql_query = call_args[0][0]
    assert "COSINE_DISTANCE" in gql_query
    assert call_args[1]['params']['embedding'] == [0.1, 0.2, 0.3]
