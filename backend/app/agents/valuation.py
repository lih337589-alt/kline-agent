import json

from app.agents.base import (
    AgentExecution,
    EvidenceValidationError,
)
from app.llm.client import LLMClient
from app.schemas.agent import AgentResult
from app.schemas.features import (
    ValuationFeatures,
)

_VALUATION_INSTRUCTIONS = """
You are the Valuation Agent in a financial
research system.

You receive valuation and profitability metrics
that were already calculated by deterministic
Python code.

Rules:
1. Do not invent valuation metrics.
2. Do not recalculate P/E or margins.
3. Interpret only supplied values.
4. Every evidence_id must come from
   allowed_evidence_ids.
5. Treat missing values explicitly as missing.
6. Do not issue a direct buy or sell instruction.
7. confidence must be between 0 and 1.
8. Keep the answer concise and professional.
""".strip()


class ValuationAgent:
    name = "valuation"

    def __init__(
        self,
        llm_client: LLMClient,
    ) -> None:
        self.llm_client = llm_client

    def run(
        self,
        features: ValuationFeatures,
    ) -> AgentExecution:
        allowed_evidence_ids: set[str] = set()

        if features.price_source_id:
            allowed_evidence_ids.add(features.price_source_id)

        if features.financial_source_id:
            allowed_evidence_ids.add(features.financial_source_id)

        payload = {
            "symbol": features.symbol,
            "allowed_evidence_ids": sorted(allowed_evidence_ids),
            "valuation_features": (features.model_dump(mode="json")),
        }

        result, call_info = self.llm_client.generate_structured(
            instructions=(_VALUATION_INSTRUCTIONS),
            input_text=json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            schema=AgentResult,
            schema_name=("valuation_agent_result"),
        )

        invalid_ids = set(result.evidence_ids) - allowed_evidence_ids

        if invalid_ids:
            invalid = ", ".join(sorted(invalid_ids))

            raise EvidenceValidationError(
                f"Valuation agent returned invalid evidence IDs: {invalid}"
            )

        return AgentExecution(
            agent_name=self.name,
            result=result,
            llm_call=call_info,
        )
