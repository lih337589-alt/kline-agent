import argparse
import json
from time import perf_counter
from uuid import uuid4

from sqlalchemy import select

from app.agents.base import EvidenceValidationError
from app.agents.fundamental import FundamentalAgent
from app.cache.redis import RedisCache
from app.core.config import settings
from app.database.session import SessionLocal
from app.llm.client import (
    LLMClient,
    LLMOutputError,
    LLMProviderError,
)
from app.models.stock import Stock
from app.repositories.agent_run import create_agent_run
from app.schemas.context import AnalysisContext
from app.services.context_builder import ContextBuilder


def get_stock(
    db,
    symbol: str,
) -> Stock | None:
    statement = select(Stock).where(Stock.symbol == symbol)

    return db.scalar(statement)


def build_input_summary(
    context: AnalysisContext,
) -> str:
    evidence_ids: list[str] = []

    if context.market.source_ref is not None:
        evidence_ids.append(context.market.source_ref.source_id)

    for financial in context.financials:
        evidence_ids.append(financial.source_ref.source_id)

    for text in context.texts:
        evidence_ids.append(text.source_ref.source_id)

    summary = {
        "symbol": context.symbol,
        "built_at": (context.built_at.isoformat()),
        "financial_count": len(context.financials),
        "text_count": len(context.texts),
        "evidence_ids": evidence_ids,
    }

    return json.dumps(
        summary,
        ensure_ascii=False,
        separators=(",", ":"),
    )


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

        context: AnalysisContext | None = None

        input_summary: str | None = None

        agent_started_at = perf_counter()

        try:
            context = context_builder.build(
                db,
                symbol,
                use_cache=(not args.no_cache),
            )

            input_summary = build_input_summary(context)

            llm_client = LLMClient(
                api_key=(settings.llm_api_key),
                base_url=(settings.llm_base_url),
                model=settings.llm_model,
                timeout_seconds=(settings.llm_timeout_seconds),
            )

            agent = FundamentalAgent(llm_client)

            execution = agent.run(context)

        except (
            LookupError,
            ValueError,
            LLMProviderError,
            LLMOutputError,
            EvidenceValidationError,
        ) as exc:
            duration_ms = int((perf_counter() - agent_started_at) * 1000)

            if input_summary is None:
                input_summary = json.dumps(
                    {
                        "symbol": symbol,
                        "context_available": (context is not None),
                    },
                    ensure_ascii=False,
                )

            try:
                agent_run = create_agent_run(
                    db,
                    stock_id=stock.id,
                    trace_id=trace_id,
                    agent_type="fundamental",
                    model_name=(settings.llm_model),
                    status="error",
                    input_summary=(input_summary),
                    output_json=None,
                    error_message=str(exc),
                    duration_ms=duration_ms,
                    token_count=None,
                    source=(settings.llm_provider),
                )

                agent_run_id = agent_run.id

                db.commit()

            except Exception:
                db.rollback()
                raise

            print(
                "status=error "
                f"symbol={symbol} "
                f"trace_id={trace_id} "
                f"agent_run_id={agent_run_id} "
                f"reason={exc}"
            )

            raise SystemExit(1) from exc

        try:
            agent_run = create_agent_run(
                db,
                stock_id=stock.id,
                trace_id=trace_id,
                agent_type=(execution.agent_name),
                model_name=(execution.llm_call.model),
                status="success",
                input_summary=(input_summary),
                output_json=(execution.result.model_dump_json()),
                error_message=None,
                duration_ms=(execution.llm_call.elapsed_ms),
                token_count=(execution.llm_call.total_tokens),
                source=(settings.llm_provider),
            )

            agent_run_id = agent_run.id

            db.commit()

        except Exception:
            db.rollback()
            raise

    print(
        "status=ok "
        f"symbol={symbol} "
        "agent=fundamental "
        f"trace_id={trace_id} "
        f"agent_run_id={agent_run_id} "
        "context_cache_hit="
        f"{str(context_builder.last_cache_hit).lower()}"
    )

    print(execution.result.model_dump_json(indent=2))

    info = execution.llm_call

    print(
        "llm_usage "
        f"model={info.model} "
        f"elapsed_ms={info.elapsed_ms} "
        f"input_tokens={info.input_tokens} "
        f"output_tokens={info.output_tokens} "
        f"total_tokens={info.total_tokens}"
    )


if __name__ == "__main__":
    main()
