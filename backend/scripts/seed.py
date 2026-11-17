from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models import News, Price, Stock

SEED_TIMESTAMP = datetime(
    2026,
    1,
    2,
    21,
    0,
    tzinfo=UTC,
)

SEED_NEWS_TIME = datetime(
    2026,
    1,
    2,
    20,
    0,
    tzinfo=UTC,
)


SEED_STOCKS = [
    (
        "AAPL",
        "Apple Inc.",
        "NASDAQ",
        "Technology",
        Decimal("100.00"),
    ),
    (
        "MSFT",
        "Microsoft Corporation",
        "NASDAQ",
        "Technology",
        Decimal("200.00"),
    ),
    (
        "NVDA",
        "NVIDIA Corporation",
        "NASDAQ",
        "Technology",
        Decimal("300.00"),
    ),
]


def main() -> None:
    with SessionLocal() as session:
        for (
            symbol,
            name,
            exchange,
            industry,
            close_price,
        ) in SEED_STOCKS:
            stock = session.scalar(select(Stock).where(Stock.symbol == symbol))

            if stock is None:
                stock = Stock(
                    symbol=symbol,
                    name=name,
                    exchange=exchange,
                    industry=industry,
                )

                session.add(stock)
                session.flush()

            price = session.scalar(
                select(Price).where(
                    Price.stock_id == stock.id,
                    Price.timestamp == SEED_TIMESTAMP,
                    Price.source == "seed-demo",
                )
            )

            if price is None:
                session.add(
                    Price(
                        stock_id=stock.id,
                        timestamp=SEED_TIMESTAMP,
                        open=close_price - Decimal("1.00"),
                        high=close_price + Decimal("2.00"),
                        low=close_price - Decimal("2.00"),
                        close=close_price,
                        volume=1000000,
                        source="seed-demo",
                    )
                )

            news_title = f"Demo seed news for {symbol}"

            news = session.scalar(
                select(News).where(
                    News.stock_id == stock.id,
                    News.title == news_title,
                    News.source == "seed-demo",
                )
            )

            if news is None:
                session.add(
                    News(
                        stock_id=stock.id,
                        title=news_title,
                        content=("Synthetic seed data for local development."),
                        source="seed-demo",
                        source_url=None,
                        published_at=SEED_NEWS_TIME,
                    )
                )

        session.commit()

    print("Seed complete: 3 stocks with demo price/news data.")


if __name__ == "__main__":
    main()
