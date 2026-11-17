from datetime import (
    date,
    datetime,
    timezone,
)

import pytest

from app.agents.base import (
    EvidenceValidationError,
)
from app.agents.fundamental import (
    FundamentalAgent,
)
from app.llm.client import LLMCallInfo
from app.schemas.agent import AgentResult
from app.schemas.context import (
    AnalysisContext,
    ContextTextEvidence,
    FinancialEvidence,
    MarketSnapshot,
    SourceReference,
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
                output_tokens=10,
                total_tokens=20,
            ),
        )


def make_context() -> AnalysisContext:
    financial_ref = SourceReference(
        source_id="financial:1",
        source="test",
        source_url=None,
        time=datetime(
            2025,
            12,
            31,
            tzinfo=timezone.utc,
        ),
    )

    news_ref = SourceReference(
        source_id="news:1",
        source="test",
        source_url=("https://example.test/news"),
        time=datetime(
            2026,
            9,
            10,
            tzinfo=timezone.utc,
        ),
    )

    return AnalysisContext(
        symbol="AAPL",
        company_name="Apple Test",
        built_at=datetime.now(timezone.utc),
        market=MarketSnapshot(),
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
                operating_cash_flow=120.0,
                source_ref=financial_ref,
            )
        ],
        texts=[
            ContextTextEvidence(
                category="news",
                title="Test news",
                content="Test content",
                source_ref=news_ref,
            )
        ],
    )


def test_fundamental_agent_accepts_valid_evidence() -> None:
    result = AgentResult(
        summary="Fundamentals are stable.",
        positives=["Positive cash flow"],
        negatives=[],
        evidence_ids=["financial:1"],
        confidence=0.8,
        limitations=[],
    )

    agent = FundamentalAgent(FakeLLMClient(result))

    execution = agent.run(make_context())

    assert execution.result.evidence_ids == ["financial:1"]


def test_fundamental_agent_rejects_fake_evidence() -> None:
    result = AgentResult(
        summary="Test",
        positives=[],
        negatives=[],
        evidence_ids=["financial:999"],
        confidence=0.5,
        limitations=[],
    )

    agent = FundamentalAgent(FakeLLMClient(result))

    with pytest.raises(EvidenceValidationError):
        agent.run(make_context())
