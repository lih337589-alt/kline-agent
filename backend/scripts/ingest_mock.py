from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.providers.mock import MockProvider
from app.database.session import SessionLocal
from app.models import Financial, News, Price, Stock

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures"

SYMBOLS = [
    "AAPL",
    "MSFT",
]


def get_stock(
    db: Session,
    symbol: str,
) -> Stock:
    stock = db.scalar(select(Stock).where(Stock.symbol == symbol))

    if stock is None:
        raise RuntimeError(
            f"Stock '{symbol}' not found. Run python -m scripts.seed first."
        )

    return stock


def ingest_market_data(
    db: Session,
    provider: MockProvider,
    stock: Stock,
) -> int:
    inserted = 0

    records = provider.get_market_data(stock.symbol)

    for record in records:
        existing = db.scalar(
            select(Price).where(
                Price.stock_id == stock.id,
                Price.timestamp == record.timestamp,
                Price.source == record.source,
            )
        )

        if existing is not None:
            continue

        db.add(
            Price(
                stock_id=stock.id,
                timestamp=record.timestamp,
                open=Decimal(str(record.value["open"])),
                high=Decimal(str(record.value["high"])),
                low=Decimal(str(record.value["low"])),
                close=Decimal(str(record.value["close"])),
                volume=int(record.value["volume"]),
                source=record.source,
            )
        )

        inserted += 1

    return inserted


def ingest_financial_data(
    db: Session,
    provider: MockProvider,
    stock: Stock,
) -> int:
    inserted = 0

    records = provider.get_financial_data(stock.symbol)

    for record in records:
        period_end = record.timestamp.date()
        period_type = str(record.value["period_type"])

        existing = db.scalar(
            select(Financial).where(
                Financial.stock_id == stock.id,
                Financial.period_end == period_end,
                Financial.period_type == period_type,
                Financial.source == record.source,
            )
        )

        if existing is not None:
            continue

        db.add(
            Financial(
                stock_id=stock.id,
                period_end=period_end,
                period_type=period_type,
                revenue=Decimal(str(record.value["revenue"])),
                net_income=Decimal(str(record.value["net_income"])),
                eps=Decimal(str(record.value["eps"])),
                roe=Decimal(str(record.value["roe"])),
                operating_cash_flow=Decimal(str(record.value["operating_cash_flow"])),
                source=record.source,
            )
        )

        inserted += 1

    return inserted


def ingest_news(
    db: Session,
    provider: MockProvider,
    stock: Stock,
) -> int:
    inserted = 0

    records = provider.get_news(stock.symbol)

    for record in records:
        title = str(record.value["title"])

        existing = db.scalar(
            select(News).where(
                News.stock_id == stock.id,
                News.title == title,
                News.source == record.source,
                News.published_at == record.timestamp,
            )
        )

        if existing is not None:
            continue

        db.add(
            News(
                stock_id=stock.id,
                title=title,
                content=str(record.value["content"]),
                source=record.source,
                source_url=str(record.value["source_url"]),
                published_at=record.timestamp,
            )
        )

        inserted += 1

    return inserted


def main() -> None:
    provider = MockProvider(FIXTURE_DIR)

    price_count = 0
    financial_count = 0
    news_count = 0

    with SessionLocal() as db:
        for symbol in SYMBOLS:
            stock = get_stock(
                db,
                symbol,
            )

            price_count += ingest_market_data(
                db,
                provider,
                stock,
            )

            financial_count += ingest_financial_data(
                db,
                provider,
                stock,
            )

            news_count += ingest_news(
                db,
                provider,
                stock,
            )

        db.commit()

    print(
        "Mock ingestion complete: "
        f"prices={price_count}, "
        f"financials={financial_count}, "
        f"news={news_count}"
    )


if __name__ == "__main__":
    main()
