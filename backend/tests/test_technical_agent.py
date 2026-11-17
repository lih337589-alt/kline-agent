import pytest

from app.agents.base import (
    EvidenceValidationError,
)
from app.agents.technical import (
    TechnicalAgent,
)
from app.llm.client import LLMCallInfo
from app.schemas.agent import AgentResult
from app.schemas.features import (
    TechnicalFeatures,
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


def make_features() -> TechnicalFeatures:
    return TechnicalFeatures(
        symbol="AAPL",
        latest_close=120.0,
        return_1d_pct=1.0,
        return_5d_pct=5.0,
        return_20d_pct=10.0,
        sma_5=118.0,
        sma_20=110.0,
        volatility_20d_pct=20.0,
        average_volume_5d=1_500_000.0,
        average_volume_20d=1_000_000.0,
        volume_ratio_5d_20d=1.5,
        price_points_used=21,
        source_id="price:1",
    )


def test_technical_agent_accepts_valid_evidence() -> None:
    result = AgentResult(
        summary="Technical trend is positive.",
        positives=["Price is above its moving averages."],
        negatives=["Volatility remains material."],
        evidence_ids=["price:1"],
        confidence=0.8,
        limitations=[],
    )

    agent = TechnicalAgent(FakeLLMClient(result))

    execution = agent.run(make_features())

    assert execution.agent_name == "technical"

    assert execution.result.evidence_ids == ["price:1"]

    assert execution.llm_call.total_tokens == 30


def test_technical_agent_rejects_fake_evidence() -> None:
    result = AgentResult(
        summary="Test",
        positives=[],
        negatives=[],
        evidence_ids=["price:999"],
        confidence=0.5,
        limitations=[],
    )

    agent = TechnicalAgent(FakeLLMClient(result))

    with pytest.raises(EvidenceValidationError):
        agent.run(make_features())
