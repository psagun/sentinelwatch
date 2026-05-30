"""Investigation agent for ad-hoc threat analysis.

Triggered on-demand to deep-dive into specific indicators using
the ReAct pattern: Reason → Act (fetch web data) → Observe → Repeat.

Integrates:
- Bright Data MCP Server for live web access during investigation
- AI/ML API for reasoning and verdict generation
- Cognee for consulting past investigation context
"""

import logging
from typing import Any, Dict, Optional

from src.intelligence.investigation_agent import InvestigationAgent
from src.memory.cognee_client import cognee

logger = logging.getLogger(__name__)


class InvestigationOrchestrator:
    """Orchestrates autonomous investigations with memory and context."""

    def __init__(self):
        self.agent = InvestigationAgent()

    async def investigate(
        self,
        indicator: str,
        indicator_type: str = "ip",
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run a full investigation with memory-enhanced context."""
        logger.info(
            f"Investigation requested: {indicator_type} = {indicator}"
        )

        # Step 1: Check Cognee memory for prior context
        similar = await cognee.get_similar_findings(
            {"indicator": indicator, "type": indicator_type}
        )
        if similar:
            logger.info(
                f"Found {len(similar)} similar past investigations"
            )

        # Step 2: Run the investigation agent
        result = await self.agent.investigate(
            indicator=indicator,
            indicator_type=indicator_type,
            context=context or self._build_context(similar),
        )

        result_dict = result.to_dict()

        # Step 3: Store result in Cognee memory
        await cognee.store_finding(
            entity_id=indicator,
            finding_type="investigation",
            content=result_dict,
        )

        # Step 4: Update knowledge graph
        await cognee.update_knowledge_graph(
            entities=[
                {"id": indicator, "type": indicator_type},
            ],
            relationships=[
                {"source": indicator, "target": e,
                 "type": "associated_with"}
                for e in result.affected_entities
            ],
        )

        return result_dict

    def _build_context(
        self, similar: list
    ) -> Optional[str]:
        """Build context string from similar past investigations."""
        if not similar:
            return None
        summaries = []
        for s in similar[:3]:
            content = s.get("content", {})
            summaries.append(
                f"Past: {content.get('verdict', 'unknown')} — "
                f"{content.get('indicator', '')}"
            )
        return "Previous findings:\n" + "\n".join(summaries)


# Singleton for reuse
investigation_orchestrator = InvestigationOrchestrator()
