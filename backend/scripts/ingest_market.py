import argparse
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.data.providers.alpha_vantage_common import (
    AlphaVantageClient,
)
from app.data.providers.base import (
    ProviderError,
    ProviderRecord,
)
from app.data.providers.market_alpha_vantage import (
    AlphaVantageMarketProvider,
)
from app.database.session import SessionLocal
from app.models import Price, Stock

logger = get_logger(__name__)


def get_stock_by_symbol(
    db: Session,
    symbol: str,
) -> Stock | None:
    statement = select(Stock).where(Stock.symbol == symbol)

    return db.scalar(statement)


def ingest_market_records(
    db: Session,
    stock: Stock,
    records: list[ProviderRecord],
) -> tuple[int, int]:
    inserted = 0
    skipped = 0

    seen_keys: set[tuple[int, object, str]] = set()

    for record in records:
        unique_key = (
            stock.id,
            record.timestamp,
            record.source,
        )

        if unique_key in seen_keys:
            skipped += 1
            continue

        existing = db.scalar(
            select(Price).where(
                Price.stock_id == stock.id,
                Price.timestamp == record.timestamp,
                Price.source == record.source,
            )
        )

        if existing is not None:
            seen_keys.add(unique_key)
            skipped += 1
            continue

        value = record.value

        close_price = _decimal_or_none(value.get("close"))

        if close_price is None:
            logger.warning(
                "Skipping market record "
                "without close price: "
                "symbol=%s timestamp=%s "
                "source=%s",
                stock.symbol,
                record.timestamp,
                record.source,
            )

            skipped += 1
            continue

        price = Price(
            stock_id=stock.id,
            timestamp=record.timestamp,
            open=_decimal_or_none(value.get("open")),
            high=_decimal_or_none(value.get("high")),
            low=_decimal_or_none(value.get("low")),
            close=close_price,
            volume=_int_or_none(value.get("volume")),
            source=record.source,
        )

        db.add(price)

        seen_keys.add(unique_key)
        inserted += 1

    return inserted, skipped


def main() -> None:
    configure_logging()

    parser = argparse.ArgumentParser(
        description=("Fetch market data from Alpha Vantage and store it in PostgreSQL.")
    )

    parser.add_argument(
        "symbol",
        nargs="?",
        default="AAPL",
        help="Stock symbol, for example AAPL",
    )

    args = parser.parse_args()

    symbol = args.symbol.strip().upper()

    if not symbol:
        print("status=error reason=empty_symbol")
        raise SystemExit(2)

    if not settings.alpha_vantage_api_key:
        print(f"status=error symbol={symbol} reason=missing_api_key")
        raise SystemExit(2)

    client = AlphaVantageClient(settings.alpha_vantage_api_key)

    provider = AlphaVantageMarketProvider(client)

    try:
        records = provider.get_market_data(symbol)

    except ProviderError as exc:
        logger.error(
            "Market provider failed: symbol=%s error=%s",
            symbol,
            exc,
        )

        print(f"status=error symbol={symbol} provider=alpha_vantage reason={exc}")

        raise SystemExit(1) from exc

    if not records:
        print(
            "status=error "
            f"symbol={symbol} "
            "provider=alpha_vantage "
            "reason=no_market_records"
        )
        raise SystemExit(1)

    with SessionLocal() as db:
        stock = get_stock_by_symbol(
            db,
            symbol,
        )

        if stock is None:
            print(
                "status=error "
                f"symbol={symbol} "
                "reason=stock_not_found "
                "hint=run_seed_first"
            )

            raise SystemExit(2)

        try:
            inserted, skipped = ingest_market_records(
                db,
                stock,
                records,
            )

            db.commit()

        except Exception:
            db.rollback()
            raise

    print(
        "status=ok "
        f"symbol={symbol} "
        "provider=alpha_vantage "
        f"fetched={len(records)} "
        f"inserted={inserted} "
        f"skipped={skipped}"
    )


def _decimal_or_none(
    value: object,
) -> Decimal | None:
    if value is None:
        return None

    return Decimal(str(value))


def _int_or_none(
    value: object,
) -> int | None:
    if value is None:
        return None

    return int(value)


if __name__ == "__main__":
    main()
