import json

from app.agents.base import (
    AgentExecution,
    EvidenceValidationError,
)
from app.llm.client import LLMClient
from app.schemas.agent import AgentResult
from app.schemas.context import AnalysisContext
from app.schemas.features import (
    TechnicalFeatures,
    ValuationFeatures,
)

_RISK_INSTRUCTIONS = """
You are the Risk Agent in a financial research
system.

You receive financial evidence, recent events,
and technical and valuation features that were
already prepared by deterministic system code.

Assess:
- financial risk
- profitability and cash-flow risk
- valuation-related risk
- volatility and market-behavior risk
- event risk
- important data gaps

Rules:
1. Never invent facts, metrics, or evidence IDs.
2. Do not recalculate technical or valuation
   metrics.
3. Use only the supplied inputs.
4. Every evidence_id must be copied exactly from
   allowed_evidence_ids.
5. positives should describe risk mitigants or
   areas of resilience.
6. negatives should describe material risks.
7. limitations must identify important missing
   or weak evidence.
8. Do not make a price prediction.
9. Do not issue a buy or sell instruction.
10. confidence must be between 0 and 1.
11. Keep the answer concise and professional.
""".strip()


class RiskAgent:
    name = "risk"

    def __init__(
        self,
        llm_client: LLMClient,
    ) -> None:
        self.llm_client = llm_client

    def run(
        self,
        context: AnalysisContext,
        technical: TechnicalFeatures,
        valuation: ValuationFeatures,
    ) -> AgentExecution:
        allowed_evidence_ids = self._collect_evidence_ids(
            context,
            technical,
            valuation,
        )

        payload = {
            "symbol": context.symbol,
            "company_name": (context.company_name),
            "allowed_evidence_ids": sorted(allowed_evidence_ids),
            "market": (context.market.model_dump(mode="json")),
            "financials": [item.model_dump(mode="json") for item in context.financials],
            "recent_events": [item.model_dump(mode="json") for item in context.texts],
            "technical_features": (technical.model_dump(mode="json")),
            "valuation_features": (valuation.model_dump(mode="json")),
        }

        result, call_info = self.llm_client.generate_structured(
            instructions=(_RISK_INSTRUCTIONS),
            input_text=json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            schema=AgentResult,
            schema_name=("risk_agent_result"),
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
        technical: TechnicalFeatures,
        valuation: ValuationFeatures,
    ) -> set[str]:
        evidence_ids: set[str] = set()

        if context.market.source_ref is not None:
            evidence_ids.add(context.market.source_ref.source_id)

        for financial in context.financials:
            evidence_ids.add(financial.source_ref.source_id)

        for text in context.texts:
            evidence_ids.add(text.source_ref.source_id)

        if technical.source_id:
            evidence_ids.add(technical.source_id)

        if valuation.price_source_id:
            evidence_ids.add(valuation.price_source_id)

        if valuation.financial_source_id:
            evidence_ids.add(valuation.financial_source_id)

        return evidence_ids

    @staticmethod
    def _validate_evidence_ids(
        result: AgentResult,
        allowed_evidence_ids: set[str],
    ) -> None:
        invalid_ids = set(result.evidence_ids) - allowed_evidence_ids

        if invalid_ids:
            invalid = ", ".join(sorted(invalid_ids))

            raise EvidenceValidationError(
                "Risk agent returned "
                "evidence IDs not present "
                "in supplied evidence: "
                f"{invalid}"
            )
