import argparse
from time import perf_counter
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.base import (
    EvidenceValidationError,
)
from app.agents.technical import (
    TechnicalAgent,
)
from app.core.config import settings
from app.database.session import SessionLocal
from app.llm.client import (
    LLMClient,
    LLMOutputError,
    LLMProviderError,
)
from app.models.stock import Stock
from app.repositories.agent_run import (
    create_agent_run,
)
from app.services.feature_engineering import (
    build_technical_features,
)


def get_stock(
    db: Session,
    symbol: str,
) -> Stock | None:
    return db.scalar(select(Stock).where(Stock.symbol == symbol))


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--symbol",
        default="AAPL",
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

        features = build_technical_features(
            db,
            stock,
        )

        input_summary = features.model_dump_json()

        started_at = perf_counter()

        try:
            llm_client = LLMClient(
                api_key=(settings.llm_api_key),
                base_url=(settings.llm_base_url),
                model=(settings.llm_model),
                timeout_seconds=(settings.llm_timeout_seconds),
            )

            agent = TechnicalAgent(llm_client)

            execution = agent.run(features)

        except (
            ValueError,
            LLMProviderError,
            LLMOutputError,
            EvidenceValidationError,
        ) as exc:
            duration_ms = int((perf_counter() - started_at) * 1000)

            try:
                agent_run = create_agent_run(
                    db,
                    stock_id=stock.id,
                    trace_id=trace_id,
                    agent_type="technical",
                    model_name=(settings.llm_model),
                    status="error",
                    input_summary=(input_summary),
                    output_json=None,
                    error_message=str(exc),
                    duration_ms=(duration_ms),
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
                "agent=technical "
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
        "agent=technical "
        f"trace_id={trace_id} "
        f"agent_run_id={agent_run_id}"
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
