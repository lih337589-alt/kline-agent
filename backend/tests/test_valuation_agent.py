import pytest

from app.agents.base import (
    EvidenceValidationError,
)
from app.agents.valuation import (
    ValuationAgent,
)
from app.llm.client import LLMCallInfo
from app.schemas.agent import AgentResult
from app.schemas.features import (
    ValuationFeatures,
)


class FakeLLMClient:
    def __init__(
        self,
        result: AgentResult,
    ) -> None:
        self.result = result

    def generate_structured(
        self,
        **kwargs: object,
    ) -> tuple[
        AgentResult,
        LLMCallInfo,
    ]:
        return (
            self.result,
            LLMCallInfo(
                model="fake-model",
                elapsed_ms=1,
                input_tokens=10,
                output_tokens=20,
                total_tokens=30,
            ),
        )


def make_features() -> ValuationFeatures:
    return ValuationFeatures(
        symbol="AAPL",
        latest_close=100.0,
        period_end="2025-12-31",
        eps=5.0,
        roe=0.2,
        revenue=1000.0,
        net_income=100.0,
        operating_cash_flow=150.0,
        pe_ratio=20.0,
        net_margin_pct=10.0,
        operating_cash_flow_margin_pct=15.0,
        missing_fields=[],
        price_source_id="price:1",
        financial_source_id="financial:1",
    )


def test_valuation_agent_accepts_valid_evidence() -> None:
    result = AgentResult(
        summary="Valuation metrics are available.",
        positives=["The company is profitable."],
        negatives=["Valuation requires peer comparison."],
        evidence_ids=[
            "price:1",
            "financial:1",
        ],
        confidence=0.8,
        limitations=[],
    )

    agent = ValuationAgent(FakeLLMClient(result))

    execution = agent.run(make_features())

    assert execution.agent_name == "valuation"

    assert set(execution.result.evidence_ids) == {
        "price:1",
        "financial:1",
    }

    assert execution.llm_call.total_tokens == 30


def test_valuation_agent_rejects_fake_evidence() -> None:
    result = AgentResult(
        summary="Test",
        positives=[],
        negatives=[],
        evidence_ids=["financial:999"],
        confidence=0.5,
        limitations=[],
    )

    agent = ValuationAgent(FakeLLMClient(result))

    with pytest.raises(EvidenceValidationError):
        agent.run(make_features())
