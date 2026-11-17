import json

from app.agents.base import (
    AgentExecution,
    EvidenceValidationError,
)
from app.llm.client import LLMClient
from app.schemas.agent import AgentResult
from app.schemas.features import (
    TechnicalFeatures,
)

_TECHNICAL_INSTRUCTIONS = """
You are the Technical Agent in a financial
research system.

You receive technical indicators that were
already calculated by deterministic Python code.

Rules:
1. Do not recalculate indicators.
2. Do not invent prices, returns, moving averages,
   volatility, or volume data.
3. Explain only the supplied technical features.
4. Every evidence_id must come from
   allowed_evidence_ids.
5. Missing values must be mentioned in
   limitations when material.
6. Do not issue a direct buy or sell instruction.
7. confidence must be between 0 and 1.
8. Keep the answer concise and professional.
""".strip()


class TechnicalAgent:
    name = "technical"

    def __init__(
        self,
        llm_client: LLMClient,
    ) -> None:
        self.llm_client = llm_client

    def run(
        self,
        features: TechnicalFeatures,
    ) -> AgentExecution:
        allowed_evidence_ids: set[str] = set()

        if features.source_id:
            allowed_evidence_ids.add(features.source_id)

        payload = {
            "symbol": features.symbol,
            "allowed_evidence_ids": sorted(allowed_evidence_ids),
            "technical_features": (features.model_dump(mode="json")),
        }

        result, call_info = self.llm_client.generate_structured(
            instructions=(_TECHNICAL_INSTRUCTIONS),
            input_text=json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            schema=AgentResult,
            schema_name=("technical_agent_result"),
        )

        invalid_ids = set(result.evidence_ids) - allowed_evidence_ids

        if invalid_ids:
            invalid = ", ".join(sorted(invalid_ids))

            raise EvidenceValidationError(
                f"Technical agent returned invalid evidence IDs: {invalid}"
            )

        return AgentExecution(
            agent_name=self.name,
            result=result,
            llm_call=call_info,
        )
