from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models import Financial, News, Price, Stock

DEMO_SOURCE = "demo-fixture"
DEMO_PRICE_START = date(2026, 6, 29)
DEMO_PRICE_POINTS = 60


@dataclass(frozen=True)
class DemoProfile:
    symbol: str
    name: str
    exchange: str
    industry: str
    base_close: Decimal
    daily_drift: Decimal
    wave_size: Decimal
    base_volume: int
    revenue: Decimal
    net_income: Decimal
    eps: Decimal
    roe: Decimal
    operating_cash_flow: Decimal


DEMO_PROFILES = [
    DemoProfile(
        symbol="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        industry="Technology",
        base_close=Decimal("180.00"),
        daily_drift=Decimal("0.35"),
        wave_size=Decimal("0.20"),
        base_volume=48_000_000,
        revenue=Decimal(100000000),
        net_income=Decimal(20000000),
        eps=Decimal("5.00"),
        roe=Decimal("0.25"),
        operating_cash_flow=Decimal(25000000),
    ),
    DemoProfile(
        symbol="MSFT",
        name="Microsoft Corporation",
        exchange="NASDAQ",
        industry="Technology",
        base_close=Decimal("390.00"),
        daily_drift=Decimal("0.42"),
        wave_size=Decimal("0.18"),
        base_volume=24_000_000,
        revenue=Decimal(120000000),
        net_income=Decimal(30000000),
        eps=Decimal("6.50"),
        roe=Decimal("0.28"),
        operating_cash_flow=Decimal(36000000),
    ),
    DemoProfile(
        symbol="NVDA",
        name="NVIDIA Corporation",
        exchange="NASDAQ",
        industry="Technology",
        base_close=Decimal("140.00"),
        daily_drift=Decimal("0.55"),
        wave_size=Decimal("0.45"),
        base_volume=52_000_000,
        revenue=Decimal(90000000),
        net_income=Decimal(27000000),
        eps=Decimal("4.20"),
        roe=Decimal("0.32"),
        operating_cash_flow=Decimal(31000000),
    ),
]


DEMO_NEWS: dict[str, list[tuple[str, str, datetime]]] = {
    "AAPL": [
        (
            "Demo fixture: product demand update",
            (
                "Synthetic demo fixture describing stable product demand. "
                "This is not real company news."
            ),
            datetime(2026, 9, 17, 14, 0, tzinfo=UTC),
        ),
        (
            "Demo fixture: supply chain update",
            (
                "Synthetic demo fixture describing normal supply-chain "
                "conditions. This is not real company news."
            ),
            datetime(2026, 9, 18, 14, 0, tzinfo=UTC),
        ),
    ],
    "MSFT": [
        (
            "Demo fixture: cloud demand update",
            (
                "Synthetic demo fixture describing stable cloud demand. "
                "This is not real company news."
            ),
            datetime(2026, 9, 17, 14, 0, tzinfo=UTC),
        ),
        (
            "Demo fixture: enterprise software update",
            (
                "Synthetic demo fixture describing steady enterprise "
                "software activity. This is not real company news."
            ),
            datetime(2026, 9, 18, 14, 0, tzinfo=UTC),
        ),
    ],
    "NVDA": [
        (
            "Demo fixture: accelerator demand update",
            (
                "Synthetic demo fixture describing continued accelerator "
                "demand. This is not real company news."
            ),
            datetime(2026, 9, 17, 14, 0, tzinfo=UTC),
        ),
        (
            "Demo fixture: data-center update",
            (
                "Synthetic demo fixture describing stable data-center "
                "activity. This is not real company news."
            ),
            datetime(2026, 9, 18, 14, 0, tzinfo=UTC),
        ),
    ],
}


def get_or_create_stock(
    db: Session,
    profile: DemoProfile,
) -> Stock:
    stock = db.scalar(
        select(Stock).where(
            Stock.symbol == profile.symbol,
        )
    )

    if stock is not None:
        return stock

    stock = Stock(
        symbol=profile.symbol,
        name=profile.name,
        exchange=profile.exchange,
        industry=profile.industry,
    )
    db.add(stock)
    db.flush()

    return stock


def trading_days(
    start: date,
    count: int,
) -> list[datetime]:
    result: list[datetime] = []
    current = start

    while len(result) < count:
        if current.weekday() < 5:
            result.append(
                datetime(
                    current.year,
                    current.month,
                    current.day,
                    20,
                    0,
                    tzinfo=UTC,
                )
            )

        current += timedelta(days=1)

    return result


def seed_prices(
    db: Session,
    stock: Stock,
    profile: DemoProfile,
) -> int:
    inserted = 0

    for index, timestamp in enumerate(
        trading_days(
            DEMO_PRICE_START,
            DEMO_PRICE_POINTS,
        )
    ):
        existing = db.scalar(
            select(Price).where(
                Price.stock_id == stock.id,
                Price.timestamp == timestamp,
                Price.source == DEMO_SOURCE,
            )
        )

        if existing is not None:
            continue

        wave_step = Decimal((index % 7) - 3)

        close = (
            profile.base_close
            + profile.daily_drift * Decimal(index)
            + profile.wave_size * wave_step
        ).quantize(Decimal("0.01"))

        open_price = (close - Decimal("0.35")).quantize(Decimal("0.01"))
        high = (close + Decimal("1.20")).quantize(Decimal("0.01"))
        low = (close - Decimal("1.15")).quantize(Decimal("0.01"))

        volume = (
            profile.base_volume
            + (index % 10) * 50_000
            + (300_000 if index % 13 == 0 else 0)
        )

        db.add(
            Price(
                stock_id=stock.id,
                timestamp=timestamp,
                open=open_price,
                high=high,
                low=low,
                close=close,
                volume=volume,
                source=DEMO_SOURCE,
            )
        )
        inserted += 1

    return inserted


def seed_financial(
    db: Session,
    stock: Stock,
    profile: DemoProfile,
) -> int:
    period_end = date(2025, 12, 31)
    period_type = "annual"

    existing = db.scalar(
        select(Financial).where(
            Financial.stock_id == stock.id,
            Financial.period_end == period_end,
            Financial.period_type == period_type,
            Financial.source == DEMO_SOURCE,
        )
    )

    if existing is not None:
        return 0

    db.add(
        Financial(
            stock_id=stock.id,
            period_end=period_end,
            period_type=period_type,
            revenue=profile.revenue,
            net_income=profile.net_income,
            eps=profile.eps,
            roe=profile.roe,
            operating_cash_flow=profile.operating_cash_flow,
            source=DEMO_SOURCE,
        )
    )

    return 1


def seed_news(
    db: Session,
    stock: Stock,
) -> int:
    inserted = 0

    for index, (
        title,
        content,
        published_at,
    ) in enumerate(DEMO_NEWS[stock.symbol], start=1):
        existing = db.scalar(
            select(News).where(
                News.stock_id == stock.id,
                News.title == title,
                News.source == DEMO_SOURCE,
                News.published_at == published_at,
            )
        )

        if existing is not None:
            continue

        db.add(
            News(
                stock_id=stock.id,
                title=title,
                content=content,
                source=DEMO_SOURCE,
                source_url=(
                    f"https://example.test/demo/{stock.symbol.lower()}/{index}"
                ),
                published_at=published_at,
            )
        )
        inserted += 1

    return inserted


def main() -> None:
    price_count = 0
    financial_count = 0
    news_count = 0

    with SessionLocal() as db:
        for profile in DEMO_PROFILES:
            stock = get_or_create_stock(
                db,
                profile,
            )

            price_count += seed_prices(
                db,
                stock,
                profile,
            )

            financial_count += seed_financial(
                db,
                stock,
                profile,
            )

            news_count += seed_news(
                db,
                stock,
            )

        db.commit()

    print(
        "Demo seed complete: "
        f"stocks_ready={len(DEMO_PROFILES)}, "
        f"prices_inserted={price_count}, "
        f"financials_inserted={financial_count}, "
        f"news_inserted={news_count}"
    )


if __name__ == "__main__":
    main()
