import argparse

from app.cache.redis import RedisCache
from app.core.config import settings
from app.database.session import SessionLocal
from app.services.context_builder import ContextBuilder


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

    cache = RedisCache(settings.redis_url)

    builder = ContextBuilder(cache=cache)

    try:
        with SessionLocal() as db:
            context = builder.build(
                db,
                symbol,
                use_cache=(not args.no_cache),
            )

    except LookupError as exc:
        print(f"status=error symbol={symbol} reason={exc}")

        raise SystemExit(2) from exc

    print(f"status=ok symbol={symbol} cache_hit={str(builder.last_cache_hit).lower()}")

    print(context.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
