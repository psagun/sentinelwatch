"""Tests for Cognee persistent memory integration.

Covers:
- CogneeMemory client unit tests (store/query/context)
"""

import pytest
from unittest.mock import AsyncMock, patch

from src.memory.cognee_client import CogneeMemory


class TestCogneeMemoryClient:
    """Unit tests for the CogneeMemory client class."""

    def test_init_without_key(self, monkeypatch):
        monkeypatch.setattr("src.config.settings.cognee_api_key", "")
        memory = CogneeMemory()
        assert memory.api_key == ""

    @pytest.mark.asyncio
    async def test_store_finding_no_key(self, monkeypatch):
        monkeypatch.setattr("src.config.settings.cognee_api_key", "")
        memory = CogneeMemory()
        result = await memory.store_finding("entity-1", "test", {"key": "val"})
        assert result is False

    @pytest.mark.asyncio
    async def test_query_memory_no_key(self, monkeypatch):
        monkeypatch.setattr("src.config.settings.cognee_api_key", "")
        memory = CogneeMemory()
        results = await memory.query_memory("test query")
        assert results == []

    @pytest.mark.asyncio
    async def test_get_entity_context_no_key(self, monkeypatch):
        monkeypatch.setattr("src.config.settings.cognee_api_key", "")
        memory = CogneeMemory()
        ctx = await memory.get_entity_context("entity-1")
        assert ctx == {"entity_id": "entity-1", "memory_count": 0}

    @pytest.mark.asyncio
    async def test_update_knowledge_graph_no_key(self, monkeypatch):
        monkeypatch.setattr("src.config.settings.cognee_api_key", "")
        memory = CogneeMemory()
        result = await memory.update_knowledge_graph([], [])
        assert result is False

    @pytest.mark.asyncio
    async def test_get_similar_findings_no_key(self, monkeypatch):
        monkeypatch.setattr("src.config.settings.cognee_api_key", "")
        memory = CogneeMemory()
        results = await memory.get_similar_findings({"test": "data"})
        assert results == []

    @pytest.mark.asyncio
    async def test_store_finding_with_key(self, monkeypatch):
        monkeypatch.setattr("src.config.settings.cognee_api_key", "test-key-123")

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = AsyncMock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            memory = CogneeMemory()
            result = await memory.store_finding(
                "entity-1", "vulnerability",
                {"title": "Test Finding", "severity": "high"},
            )
            assert result is True
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_finding_api_error(self, monkeypatch):
        monkeypatch.setattr("src.config.settings.cognee_api_key", "test-key-123")

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post = AsyncMock(side_effect=Exception("API unavailable"))

        with patch("httpx.AsyncClient", return_value=mock_client):
            memory = CogneeMemory()
            result = await memory.store_finding(
                "entity-1", "test", {"key": "val"}
            )
            assert result is False

    @pytest.mark.asyncio
    async def test_query_memory_with_key(self, monkeypatch):
        monkeypatch.setattr("src.config.settings.cognee_api_key", "test-key-123")

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(return_value={
            "results": [{"title": "Found finding", "similarity": 0.92}]
        })

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            memory = CogneeMemory()
            results = await memory.query_memory(
                "security vulnerability", entity_id="entity-1", limit=5
            )
            assert len(results) == 1
            assert results[0]["title"] == "Found finding"

    @pytest.mark.asyncio
    async def test_get_entity_context_with_key(self, monkeypatch):
        monkeypatch.setattr("src.config.settings.cognee_api_key", "test-key-123")

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(return_value={
            "entity_id": "entity-1", "memory_count": 3, "findings": ["f1", "f2", "f3"],
        })

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            memory = CogneeMemory()
            ctx = await memory.get_entity_context("entity-1")
            assert ctx["memory_count"] == 3
            assert len(ctx["findings"]) == 3

    def test_headers_include_auth(self, monkeypatch):
        monkeypatch.setattr("src.config.settings.cognee_api_key", "secret-123")
        memory = CogneeMemory()
        headers = memory._headers()
        assert headers["Authorization"] == "Bearer secret-123"
        assert headers["Content-Type"] == "application/json"


class TestCogneeSingleton:
    def test_cognee_instance_exists(self):
        from src.memory.cognee_client import cognee
        assert isinstance(cognee, CogneeMemory)

    @pytest.mark.asyncio
    async def test_cognee_singleton_no_key(self, monkeypatch):
        monkeypatch.setattr("src.config.settings.cognee_api_key", "")
        from src.memory.cognee_client import cognee
        result = await cognee.store_finding("test", "test", {"k": "v"})
        assert result is False
