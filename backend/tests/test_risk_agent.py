from datetime import (
    date,
    datetime,
    timezone,
)

import pytest

from app.agents.base import (
    EvidenceValidationError,
)
from app.agents.risk import RiskAgent
from app.llm.client import LLMCallInfo
from app.schemas.agent import AgentResult
from app.schemas.context import (
    AnalysisContext,
    ContextTextEvidence,
    FinancialEvidence,
    MarketSnapshot,
    SourceReference,
)
from app.schemas.features import (
    TechnicalFeatures,
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


def make_context() -> AnalysisContext:
    financial_time = datetime(
        2025,
        12,
        31,
        tzinfo=timezone.utc,
    )

    event_time = datetime(
        2026,
        9,
        10,
        tzinfo=timezone.utc,
    )

    return AnalysisContext(
        symbol="AAPL",
        company_name="Apple Test",
        built_at=datetime.now(timezone.utc),
        market=MarketSnapshot(
            latest_close=120.0,
            source_ref=SourceReference(
                source_id="price:1",
                source="test",
                source_url=None,
                time=event_time,
            ),
        ),
        financials=[
            FinancialEvidence(
                period_end=date(
                    2025,
                    12,
                    31,
                ),
                period_type="annual",
                revenue=1000.0,
                net_income=100.0,
                eps=5.0,
                roe=0.2,
                operating_cash_flow=150.0,
                source_ref=SourceReference(
                    source_id="financial:1",
                    source="test",
                    source_url=None,
                    time=financial_time,
                ),
            )
        ],
        texts=[
            ContextTextEvidence(
                category="news",
                title="Test event",
                content="Test risk event.",
                source_ref=SourceReference(
                    source_id="news:1",
                    source="test",
                    source_url=("https://example.test/news/1"),
                    time=event_time,
                ),
            )
        ],
    )


def make_technical() -> TechnicalFeatures:
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


def make_valuation() -> ValuationFeatures:
    return ValuationFeatures(
        symbol="AAPL",
        latest_close=120.0,
        period_end="2025-12-31",
        eps=5.0,
        roe=0.2,
        revenue=1000.0,
        net_income=100.0,
        operating_cash_flow=150.0,
        pe_ratio=24.0,
        net_margin_pct=10.0,
        operating_cash_flow_margin_pct=15.0,
        missing_fields=[],
        price_source_id="price:1",
        financial_source_id="financial:1",
    )


def test_risk_agent_accepts_valid_evidence() -> None:
    result = AgentResult(
        summary=("Risk appears moderate based on supplied evidence."),
        positives=["Operating cash flow is positive."],
        negatives=["Market volatility remains material."],
        evidence_ids=[
            "financial:1",
            "price:1",
            "news:1",
        ],
        confidence=0.8,
        limitations=["The evidence window is limited."],
    )

    agent = RiskAgent(FakeLLMClient(result))

    execution = agent.run(
        make_context(),
        make_technical(),
        make_valuation(),
    )

    assert execution.agent_name == "risk"

    assert set(execution.result.evidence_ids) == {
        "financial:1",
        "price:1",
        "news:1",
    }

    assert execution.llm_call.total_tokens == 30


def test_risk_agent_rejects_fake_evidence() -> None:
    result = AgentResult(
        summary="Test",
        positives=[],
        negatives=[],
        evidence_ids=["financial:999"],
        confidence=0.5,
        limitations=[],
    )

    agent = RiskAgent(FakeLLMClient(result))

    with pytest.raises(EvidenceValidationError):
        agent.run(
            make_context(),
            make_technical(),
            make_valuation(),
        )
