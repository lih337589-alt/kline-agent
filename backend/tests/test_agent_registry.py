from datetime import (
    date,
    datetime,
    timezone,
)

from app.agents.registry import (
    AgentRegistry,
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
from app.schemas.features import (
    TechnicalFeatures,
    ValuationFeatures,
)


class FakeLLMClient:
    def __init__(self) -> None:
        self.schema_names: list[str] = []

    def generate_structured(
        self,
        *,
        schema_name: str,
        **kwargs: object,
    ) -> tuple[
        AgentResult,
        LLMCallInfo,
    ]:
        self.schema_names.append(schema_name)

        evidence_by_schema = {
            "fundamental_agent_result": ["financial:1"],
            "valuation_agent_result": [
                "price:1",
                "financial:1",
            ],
            "technical_agent_result": ["price:1"],
            "sentiment_agent_result": ["news:1"],
            "risk_agent_result": [
                "price:1",
                "financial:1",
                "news:1",
            ],
        }

        result = AgentResult(
            summary=(f"Fake result for {schema_name}"),
            positives=["Test positive"],
            negatives=["Test negative"],
            evidence_ids=(evidence_by_schema[schema_name]),
            confidence=0.8,
            limitations=["Test limitation"],
        )

        return (
            result,
            LLMCallInfo(
                model="fake-model",
                elapsed_ms=1,
                input_tokens=10,
                output_tokens=20,
                total_tokens=30,
            ),
        )


def make_context() -> AnalysisContext:
    market_time = datetime(
        2026,
        9,
        10,
        tzinfo=timezone.utc,
    )

    financial_time = datetime(
        2025,
        12,
        31,
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
                time=market_time,
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
                title="Test news",
                content="Test content.",
                source_ref=SourceReference(
                    source_id="news:1",
                    source="test",
                    source_url=("https://example.test/news/1"),
                    time=market_time,
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


def test_registry_runs_five_agents() -> None:
    fake_client = FakeLLMClient()

    registry = AgentRegistry(fake_client)

    outcomes = registry.run_all(
        context=make_context(),
        technical=make_technical(),
        valuation=make_valuation(),
    )

    assert len(outcomes) == 5

    assert [outcome.agent_name for outcome in outcomes] == [
        "fundamental",
        "valuation",
        "technical",
        "sentiment",
        "risk",
    ]

    assert all(outcome.succeeded for outcome in outcomes)

    assert all(outcome.execution is not None for outcome in outcomes)

    assert fake_client.schema_names == [
        "fundamental_agent_result",
        "valuation_agent_result",
        "technical_agent_result",
        "sentiment_agent_result",
        "risk_agent_result",
    ]
