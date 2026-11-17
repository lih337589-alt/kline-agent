import argparse
from uuid import uuid4

from sqlalchemy import select

from app.agents.sentiment import (
    SentimentAgent,
)
from app.cache.redis import RedisCache
from app.core.config import settings
from app.database.session import SessionLocal
from app.llm.client import (
    LLMClient,
    LLMLimitError,
    LLMOutputError,
    LLMProviderError,
)
from app.models.stock import Stock
from app.services.context_builder import (
    ContextBuilder,
)


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
        stock = db.scalar(select(Stock).where(Stock.symbol == symbol))

        if stock is None:
            print(
                "status=error "
                f"symbol={symbol} "
                f"trace_id={trace_id} "
                "reason=stock_not_found"
            )

            raise SystemExit(2)

        context_builder = ContextBuilder(cache=RedisCache(settings.redis_url))

        context = context_builder.build(
            db,
            symbol,
            use_cache=False,
        )

    llm_client = LLMClient(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        timeout_seconds=(settings.llm_timeout_seconds),
        max_calls=1,
    )

    agent = SentimentAgent(llm_client)

    try:
        execution = agent.run(context)

    except (
        ValueError,
        LLMLimitError,
        LLMProviderError,
        LLMOutputError,
    ) as exc:
        print(
            "status=error "
            f"symbol={symbol} "
            "agent=sentiment "
            f"trace_id={trace_id} "
            f"reason={exc}"
        )

        raise SystemExit(1) from exc

    print(
        "status=ok "
        f"symbol={symbol} "
        "agent=sentiment "
        f"trace_id={trace_id} "
        f"llm_calls={llm_client.call_count} "
        f"text_count={len(context.texts)}"
    )

    print(execution.result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
