from datetime import (
    datetime,
    timezone,
)

import pytest

from app.agents.base import (
    EvidenceValidationError,
)
from app.agents.sentiment import (
    SentimentAgent,
)
from app.llm.client import LLMCallInfo
from app.schemas.agent import AgentResult
from app.schemas.context import (
    AnalysisContext,
    ContextTextEvidence,
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
                output_tokens=20,
                total_tokens=30,
            ),
        )


def make_context() -> AnalysisContext:
    published_at = datetime(
        2026,
        9,
        10,
        tzinfo=timezone.utc,
    )

    return AnalysisContext(
        symbol="AAPL",
        company_name="Apple Test",
        built_at=datetime.now(timezone.utc),
        market=MarketSnapshot(),
        financials=[],
        texts=[
            ContextTextEvidence(
                category="news",
                title="Test positive event",
                content=("The company announced a positive test event."),
                source_ref=SourceReference(
                    source_id="news:1",
                    source="test",
                    source_url=("https://example.test/news/1"),
                    time=published_at,
                ),
            ),
            ContextTextEvidence(
                category="announcement",
                title="Test announcement",
                content=("The company published a test announcement."),
                source_ref=SourceReference(
                    source_id="announcement:2",
                    source="test",
                    source_url=("https://example.test/announcement/2"),
                    time=published_at,
                ),
            ),
        ],
    )


def test_sentiment_agent_accepts_valid_evidence() -> None:
    result = AgentResult(
        summary=("Recent event sentiment is moderately positive."),
        positives=["A positive event was reported."],
        negatives=[],
        evidence_ids=["news:1"],
        confidence=0.8,
        limitations=["The evidence window is limited."],
    )

    agent = SentimentAgent(FakeLLMClient(result))

    execution = agent.run(make_context())

    assert execution.agent_name == "sentiment"

    assert execution.result.evidence_ids == ["news:1"]

    assert execution.llm_call.total_tokens == 30


def test_sentiment_agent_rejects_fake_evidence() -> None:
    result = AgentResult(
        summary="Test",
        positives=[],
        negatives=[],
        evidence_ids=["news:999"],
        confidence=0.5,
        limitations=[],
    )

    agent = SentimentAgent(FakeLLMClient(result))

    with pytest.raises(EvidenceValidationError):
        agent.run(make_context())


def test_sentiment_agent_handles_empty_text_context() -> None:
    context = AnalysisContext(
        symbol="AAPL",
        company_name="Apple Test",
        built_at=datetime.now(timezone.utc),
        market=MarketSnapshot(),
        financials=[],
        texts=[],
    )

    result = AgentResult(
        summary=("No recent event evidence is available."),
        positives=[],
        negatives=[],
        evidence_ids=[],
        confidence=0.2,
        limitations=["No recent news or announcement evidence is available."],
    )

    agent = SentimentAgent(FakeLLMClient(result))

    execution = agent.run(context)

    assert execution.agent_name == "sentiment"

    assert execution.result.evidence_ids == []

    assert execution.result.limitations
