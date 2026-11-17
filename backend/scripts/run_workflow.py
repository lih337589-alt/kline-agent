import argparse
import json
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.registry import AgentRunOutcome
from app.cache.redis import RedisCache
from app.core.config import settings
from app.core.limits import (
    LLM_MAX_CALLS_PER_ANALYSIS,
    LLM_MAX_INPUT_CHARS,
    LLM_MAX_RETRIES,
)
from app.database.session import SessionLocal
from app.llm.client import LLMClient
from app.models.stock import Stock
from app.repositories.agent_run import create_agent_run
from app.schemas.context import AnalysisContext
from app.schemas.features import TechnicalFeatures, ValuationFeatures
from app.services.context_builder import ContextBuilder
from app.services.feature_engineering import (
    build_technical_features,
    build_valuation_features,
)
from app.workflows.analysis import AnalysisWorkflow


def get_stock(
    db: Session,
    symbol: str,
) -> Stock | None:
    return db.scalar(select(Stock).where(Stock.symbol == symbol))


def build_context_summary(
    context: AnalysisContext,
) -> dict[str, object]:
    evidence_ids: list[str] = []

    if context.market.source_ref is not None:
        evidence_ids.append(context.market.source_ref.source_id)

    evidence_ids.extend(
        financial.source_ref.source_id for financial in context.financials
    )

    evidence_ids.extend(text.source_ref.source_id for text in context.texts)

    return {
        "symbol": context.symbol,
        "built_at": context.built_at.isoformat(),
        "financial_count": len(context.financials),
        "text_count": len(context.texts),
        "evidence_ids": evidence_ids,
    }


def build_input_summaries(
    context: AnalysisContext,
    technical: TechnicalFeatures,
    valuation: ValuationFeatures,
) -> dict[str, str]:
    context_summary = build_context_summary(context)

    return {
        "fundamental": json.dumps(
            context_summary,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "valuation": valuation.model_dump_json(),
        "technical": technical.model_dump_json(),
        "sentiment": json.dumps(
            {
                "symbol": context.symbol,
                "text_count": len(context.texts),
                "evidence_ids": [item.source_ref.source_id for item in context.texts],
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "risk": json.dumps(
            {
                "context": context_summary,
                "technical": technical.model_dump(mode="json"),
                "valuation": valuation.model_dump(mode="json"),
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    }


def persist_outcomes(
    db: Session,
    *,
    stock: Stock,
    trace_id: str,
    outcomes: list[AgentRunOutcome],
    input_summaries: dict[str, str],
) -> list[int]:
    agent_run_ids: list[int] = []

    try:
        for outcome in outcomes:
            execution = outcome.execution

            if execution is not None:
                agent_run = create_agent_run(
                    db,
                    stock_id=stock.id,
                    trace_id=trace_id,
                    agent_type=outcome.agent_name,
                    model_name=execution.llm_call.model,
                    status="success",
                    input_summary=input_summaries[outcome.agent_name],
                    output_json=execution.result.model_dump_json(),
                    error_message=None,
                    duration_ms=outcome.duration_ms,
                    token_count=execution.llm_call.total_tokens,
                    source=settings.llm_provider,
                )
            else:
                agent_run = create_agent_run(
                    db,
                    stock_id=stock.id,
                    trace_id=trace_id,
                    agent_type=outcome.agent_name,
                    model_name=settings.llm_model,
                    status="error",
                    input_summary=input_summaries[outcome.agent_name],
                    output_json=None,
                    error_message=outcome.error_message,
                    duration_ms=outcome.duration_ms,
                    token_count=None,
                    source=settings.llm_provider,
                )

            agent_run_ids.append(agent_run.id)

        db.commit()

    except Exception:
        db.rollback()
        raise

    return agent_run_ids


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--symbol",
        default="AAPL",
    )

    parser.add_argument(
        "--no-cache",
        action="store_true",
    )

    args = parser.parse_args()

    symbol = args.symbol.strip().upper()
    trace_id = uuid4().hex

    with SessionLocal() as db:
        stock = get_stock(
            db,
            symbol,
        )

        if stock is None:
            print(
                "status=error "
                f"symbol={symbol} "
                f"trace_id={trace_id} "
                "reason=stock_not_found"
            )
            raise SystemExit(2)

        cache = RedisCache(settings.redis_url)

        context_builder = ContextBuilder(cache=cache)

        context = context_builder.build(
            db,
            symbol,
            use_cache=not args.no_cache,
        )

        technical = build_technical_features(
            db,
            stock,
        )

        valuation = build_valuation_features(
            db,
            stock,
        )

        llm_client = LLMClient(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            model=settings.llm_model,
            timeout_seconds=settings.llm_timeout_seconds,
            max_retries=LLM_MAX_RETRIES,
            max_calls=LLM_MAX_CALLS_PER_ANALYSIS,
            max_input_chars=LLM_MAX_INPUT_CHARS,
        )

        workflow = AnalysisWorkflow(llm_client)

        workflow_result = workflow.run(
            trace_id=trace_id,
            context=context,
            technical_features=technical,
            valuation_features=valuation,
        )

        outcomes = workflow_result.outcomes

        input_summaries = build_input_summaries(
            context,
            technical,
            valuation,
        )

        agent_run_ids = persist_outcomes(
            db,
            stock=stock,
            trace_id=trace_id,
            outcomes=outcomes,
            input_summaries=input_summaries,
        )

        success_count = sum(outcome.succeeded for outcome in outcomes)

        error_count = len(outcomes) - success_count

        debate_succeeded = (
    workflow_result.debate is not None
)

overall_status = (
    "ok"
    if (
        error_count == 0
        and debate_succeeded
    )
    else "partial"
) 
        print(
            f"status={overall_status} "
            f"symbol={symbol} "
            f"trace_id={trace_id} "
            f"agents={len(outcomes)} "
            f"success={success_count} "
            f"error={error_count} "
            f"llm_calls={llm_client.call_count} "
            "context_cache_hit="
            f"{str(context_builder.last_cache_hit).lower()}"
        )

        print(
            "agent_run_ids="
            + ",".join(str(agent_run_id) for agent_run_id in agent_run_ids)
        )

        for outcome in outcomes:
            print()
            print(f"agent={outcome.agent_name}")

            if outcome.execution is None:
                print(f"status=error reason={outcome.error_message}")
                continue

            print("status=success")
            print(outcome.execution.result.model_dump_json(indent=2))

        if error_count:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
