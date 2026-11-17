from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select

from app.agents.base import AgentExecution
from app.agents.registry import (
    AgentRegistry,
    AgentRunOutcome,
)
from app.core.limits import (
    LLM_MAX_CALLS_PER_ANALYSIS,
)
from app.database.session import SessionLocal
from app.llm.client import (
    LLMCallInfo,
    LLMProviderError,
)
from app.models.agent_run import AgentRun
from app.models.stock import Stock
from app.schemas.agent import AgentResult
from app.schemas.context import (
    AnalysisContext,
    MarketSnapshot,
)
from app.schemas.features import (
    TechnicalFeatures,
    ValuationFeatures,
)
from scripts.run_agents import persist_outcomes


def make_result(
    summary: str = "Test result",
) -> AgentResult:
    return AgentResult(
        summary=summary,
        positives=[],
        negatives=[],
        evidence_ids=[],
        confidence=0.5,
        limitations=["Insufficient evidence."],
    )


def make_call_info() -> LLMCallInfo:
    return LLMCallInfo(
        model="fake-model",
        elapsed_ms=1,
        input_tokens=10,
        output_tokens=20,
        total_tokens=30,
    )


def make_empty_context() -> AnalysisContext:
    return AnalysisContext(
        symbol="TEST",
        company_name="Test Company",
        built_at=datetime.now(timezone.utc),
        market=MarketSnapshot(),
        financials=[],
        texts=[],
    )


def make_empty_technical() -> TechnicalFeatures:
    return TechnicalFeatures(
        symbol="TEST",
    )


def make_empty_valuation() -> ValuationFeatures:
    return ValuationFeatures(
        symbol="TEST",
        missing_fields=["financials"],
    )


class NoDataFakeLLMClient:
    def generate_structured(
        self,
        **kwargs: object,
    ) -> tuple[
        AgentResult,
        LLMCallInfo,
    ]:
        return (
            make_result(),
            make_call_info(),
        )


class OneFailureFakeLLMClient:
    def generate_structured(
        self,
        *,
        schema_name: str,
        **kwargs: object,
    ) -> tuple[
        AgentResult,
        LLMCallInfo,
    ]:
        if schema_name == "sentiment_agent_result":
            raise LLMProviderError("simulated provider failure")

        return (
            make_result(),
            make_call_info(),
        )


def test_max_calls_is_explicit() -> None:
    assert LLM_MAX_CALLS_PER_ANALYSIS == 9


def test_registry_handles_no_data() -> None:
    registry = AgentRegistry(NoDataFakeLLMClient())

    outcomes = registry.run_all(
        context=make_empty_context(),
        technical=(make_empty_technical()),
        valuation=(make_empty_valuation()),
    )

    assert len(outcomes) == 5

    assert all(outcome.succeeded for outcome in outcomes)

    for outcome in outcomes:
        assert outcome.execution is not None

        assert outcome.execution.result.limitations


def test_registry_continues_after_model_failure() -> None:
    registry = AgentRegistry(OneFailureFakeLLMClient())

    outcomes = registry.run_all(
        context=make_empty_context(),
        technical=(make_empty_technical()),
        valuation=(make_empty_valuation()),
    )

    assert len(outcomes) == 5

    failed = [outcome for outcome in outcomes if not outcome.succeeded]

    succeeded = [outcome for outcome in outcomes if outcome.succeeded]

    assert len(failed) == 1

    assert failed[0].agent_name == "sentiment"

    assert len(succeeded) == 4

    assert [outcome.agent_name for outcome in outcomes] == [
        "fundamental",
        "valuation",
        "technical",
        "sentiment",
        "risk",
    ]


def test_model_failure_does_not_break_transaction() -> None:
    symbol = "D" + uuid4().hex[:8].upper()

    trace_id = uuid4().hex

    with SessionLocal() as db:
        stock = Stock(
            symbol=symbol,
            name="Day 14 Test Stock",
            exchange="TEST",
            industry="Testing",
        )

        db.add(stock)
        db.commit()
        db.refresh(stock)

        try:
            success_execution = AgentExecution(
                agent_name="fundamental",
                result=make_result("Successful result"),
                llm_call=(make_call_info()),
            )

            outcomes = [
                AgentRunOutcome(
                    agent_name="fundamental",
                    execution=(success_execution),
                    error_message=None,
                    duration_ms=1,
                ),
                AgentRunOutcome(
                    agent_name="sentiment",
                    execution=None,
                    error_message=("simulated failure"),
                    duration_ms=2,
                ),
            ]

            input_summaries = {
                "fundamental": ('{"symbol":"TEST"}'),
                "sentiment": ('{"symbol":"TEST"}'),
            }

            agent_run_ids = persist_outcomes(
                db,
                stock=stock,
                trace_id=trace_id,
                outcomes=outcomes,
                input_summaries=(input_summaries),
            )

            assert len(agent_run_ids) == 2

            stored = list(
                db.scalars(
                    select(AgentRun)
                    .where(AgentRun.trace_id == trace_id)
                    .order_by(AgentRun.id)
                )
            )

            assert len(stored) == 2

            assert [item.status for item in stored] == [
                "success",
                "error",
            ]

            assert stored[0].output_json is not None

            assert stored[1].error_message == "simulated failure"

        finally:
            db.delete(stock)
            db.commit()
