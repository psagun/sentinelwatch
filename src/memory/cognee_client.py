"""Cognee integration for persistent agent memory.

Provides memory and context across investigation workflows,
enabling agents to remember past findings and improve over time.
"""

import json
import logging
from typing import Any, Dict, List, Optional

import httpx

from src.config import settings

logger = logging.getLogger(__name__)


class CogneeMemory:
    """Client for Cognee agent memory and knowledge management."""

    def __init__(self):
        self.api_key = settings.cognee_api_key
        self.api_base = settings.cognee_api_base

    async def store_finding(
        self,
        entity_id: str,
        finding_type: str,
        content: Dict[str, Any],
    ) -> bool:
        """Store a finding in Cognee memory for future retrieval."""
        if not self.api_key:
            logger.debug("Cognee not configured — skipping memory store")
            return False

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.api_base}/memory",
                    headers=self._headers(),
                    json={
                        "entity_id": entity_id,
                        "finding_type": finding_type,
                        "content": content,
                    },
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.warning(f"Failed to store in Cognee memory: {e}")
            return False

    async def query_memory(
        self,
        query: str,
        entity_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Query Cognee memory for context related to a query."""
        if not self.api_key:
            return []

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.api_base}/query",
                    headers=self._headers(),
                    json={
                        "query": query,
                        "entity_id": entity_id,
                        "limit": limit,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data.get("results", [])
        except Exception as e:
            logger.warning(f"Failed to query Cognee memory: {e}")
            return []

    async def get_entity_context(
        self, entity_id: str
    ) -> Dict[str, Any]:
        """Get full memory context for an entity."""
        if not self.api_key:
            return {"entity_id": entity_id, "memory_count": 0}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.api_base}/memory/{entity_id}",
                    headers=self._headers(),
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to get entity context: {e}")
            return {"entity_id": entity_id, "memory_count": 0}

    async def update_knowledge_graph(
        self,
        entities: List[Dict[str, str]],
        relationships: List[Dict[str, str]],
    ) -> bool:
        """Update the Cognee knowledge graph with entity relationships."""
        if not self.api_key:
            return False

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_base}/knowledge-graph",
                    headers=self._headers(),
                    json={
                        "entities": entities,
                        "relationships": relationships,
                    },
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.warning(f"Failed to update knowledge graph: {e}")
            return False

    async def get_similar_findings(
        self, finding: Dict[str, Any], threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Retrieve similar past findings using semantic search."""
        if not self.api_key:
            return []

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.api_base}/similar",
                    headers=self._headers(),
                    json={
                        "finding": finding,
                        "threshold": threshold,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data.get("results", [])
        except Exception as e:
            logger.warning(f"Failed to get similar findings: {e}")
            return []

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }


cognee = CogneeMemory()
