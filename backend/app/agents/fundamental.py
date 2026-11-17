import json

from app.agents.base import (
    AgentExecution,
    EvidenceValidationError,
)
from app.llm.client import LLMClient
from app.schemas.agent import AgentResult
from app.schemas.context import AnalysisContext

_FUNDAMENTAL_INSTRUCTIONS = """
You are the Fundamental Agent in a financial
research system.

Analyze only the evidence supplied in the input.

Focus primarily on:
- financial performance
- profitability
- cash flow
- fundamental strengths
- fundamental weaknesses
- material company events when relevant

Rules:
1. Never invent facts.
2. Never invent evidence IDs.
3. Every evidence_id must be copied exactly from
   allowed_evidence_ids.
4. If data is missing, clearly state that in
   limitations.
5. Do not issue a buy or sell instruction.
6. confidence must be between 0 and 1.
7. Keep the analysis concise and professional.
""".strip()


class FundamentalAgent:
    name = "fundamental"

    def __init__(
        self,
        llm_client: LLMClient,
    ) -> None:
        self.llm_client = llm_client

    def run(
        self,
        context: AnalysisContext,
    ) -> AgentExecution:
        allowed_evidence_ids = self._collect_evidence_ids(context)

        input_text = self._build_input(
            context,
            allowed_evidence_ids,
        )

        result, call_info = self.llm_client.generate_structured(
            instructions=(_FUNDAMENTAL_INSTRUCTIONS),
            input_text=input_text,
            schema=AgentResult,
            schema_name=("fundamental_agent_result"),
        )

        self._validate_evidence_ids(
            result,
            allowed_evidence_ids,
        )

        return AgentExecution(
            agent_name=self.name,
            result=result,
            llm_call=call_info,
        )

    @staticmethod
    def _collect_evidence_ids(
        context: AnalysisContext,
    ) -> set[str]:
        evidence_ids: set[str] = set()

        if context.market.source_ref is not None:
            evidence_ids.add(context.market.source_ref.source_id)

        for financial in context.financials:
            evidence_ids.add(financial.source_ref.source_id)

        for text in context.texts:
            evidence_ids.add(text.source_ref.source_id)

        return evidence_ids

    @staticmethod
    def _build_input(
        context: AnalysisContext,
        allowed_evidence_ids: set[str],
    ) -> str:
        payload = {
            "symbol": context.symbol,
            "company_name": (context.company_name),
            "built_at": (context.built_at.isoformat()),
            "allowed_evidence_ids": (sorted(allowed_evidence_ids)),
            "market": (context.market.model_dump(mode="json")),
            "financials": [item.model_dump(mode="json") for item in context.financials],
            "texts": [item.model_dump(mode="json") for item in context.texts],
        }

        return json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    @staticmethod
    def _validate_evidence_ids(
        result: AgentResult,
        allowed_evidence_ids: set[str],
    ) -> None:
        invalid_ids = set(result.evidence_ids) - allowed_evidence_ids

        if invalid_ids:
            invalid = ", ".join(sorted(invalid_ids))

            raise EvidenceValidationError(
                f"Agent returned evidence IDs not present in context: {invalid}"
            )
