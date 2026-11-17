import argparse
from decimal import Decimal, InvalidOperation

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
from app.data.providers.financial_alpha_vantage import (
    AlphaVantageFinancialProvider,
)
from app.database.session import SessionLocal
from app.models import Financial, Stock

logger = get_logger(__name__)


def get_stock_by_symbol(
    db: Session,
    symbol: str,
) -> Stock | None:
    statement = select(Stock).where(Stock.symbol == symbol)

    return db.scalar(statement)


def ingest_financial_records(
    db: Session,
    stock: Stock,
    records: list[ProviderRecord],
) -> tuple[int, int]:
    """
    Write normalized financial records into PostgreSQL.

    Returns:
        (inserted_count, skipped_count)

    A record is considered duplicated when:
        stock_id + period_end + period_type + source
    already exists.
    """

    inserted = 0
    skipped = 0

    # Prevent duplicates that may exist inside
    # the same provider response.
    seen_keys: set[tuple[int, object, str, str]] = set()

    for record in records:
        value = record.value

        raw_period_type = value.get("period_type")

        if raw_period_type is None:
            logger.warning(
                "Skipping financial record "
                "without period_type: "
                "symbol=%s timestamp=%s "
                "source=%s",
                stock.symbol,
                record.timestamp,
                record.source,
            )

            skipped += 1
            continue

        period_type = str(raw_period_type).strip().lower()

        if not period_type:
            logger.warning(
                "Skipping financial record "
                "with empty period_type: "
                "symbol=%s timestamp=%s "
                "source=%s",
                stock.symbol,
                record.timestamp,
                record.source,
            )

            skipped += 1
            continue

        period_end = record.timestamp.date()

        unique_key = (
            stock.id,
            period_end,
            period_type,
            record.source,
        )

        if unique_key in seen_keys:
            skipped += 1
            continue

        existing = db.scalar(
            select(Financial).where(
                Financial.stock_id == stock.id,
                Financial.period_end == period_end,
                Financial.period_type == period_type,
                Financial.source == record.source,
            )
        )

        if existing is not None:
            seen_keys.add(unique_key)
            skipped += 1
            continue

        financial = Financial(
            stock_id=stock.id,
            period_end=period_end,
            period_type=period_type,
            revenue=_decimal_or_none(value.get("revenue")),
            net_income=_decimal_or_none(value.get("net_income")),
            eps=_decimal_or_none(value.get("eps")),
            roe=_decimal_or_none(value.get("roe")),
            operating_cash_flow=(_decimal_or_none(value.get("operating_cash_flow"))),
            source=record.source,
        )

        db.add(financial)

        seen_keys.add(unique_key)
        inserted += 1

    return inserted, skipped


def main() -> None:
    configure_logging()

    parser = argparse.ArgumentParser(
        description=(
            "Fetch financial data from Alpha Vantage and store it in PostgreSQL."
        )
    )

    parser.add_argument(
        "symbol",
        nargs="?",
        default="AAPL",
        help=("Stock symbol, for example AAPL"),
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

    provider = AlphaVantageFinancialProvider(client)

    try:
        records = provider.get_financial_data(symbol)

    except ProviderError as exc:
        logger.error(
            "Financial provider failed: symbol=%s error=%s",
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
            "reason=no_financial_records"
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
            inserted, skipped = ingest_financial_records(
                db,
                stock,
                records,
            )

            db.commit()

        except Exception as exc:
            db.rollback()

            logger.exception(
                "Financial database write failed: symbol=%s",
                symbol,
            )

            print(f"status=error symbol={symbol} reason=database_write_failed")

            raise SystemExit(1) from exc

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

    text = str(value).strip()

    if text.lower() in {
        "",
        "none",
        "null",
        "nan",
        "inf",
        "-inf",
        "infinity",
        "-infinity",
    }:
        return None

    try:
        return Decimal(text)

    except InvalidOperation as exc:
        raise ValueError(f"Invalid numeric financial value: {value!r}") from exc


if __name__ == "__main__":
    main()
