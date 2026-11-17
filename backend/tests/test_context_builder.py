from datetime import (
    date,
    datetime,
    timedelta,
    timezone,
)
from decimal import Decimal
from uuid import uuid4

from app.database.session import SessionLocal
from app.models import (
    Announcement,
    Financial,
    News,
    Price,
    Stock,
)
from app.services.context_builder import (
    ContextBuilder,
)


class FakeCache:
    def __init__(self) -> None:
        self.values: dict[
            str,
            str,
        ] = {}

    def get(
        self,
        key: str,
    ) -> str | None:
        return self.values.get(key)

    def set(
        self,
        key: str,
        value: str,
        ttl_seconds: int | None = None,
    ) -> None:
        self.values[key] = value


def test_context_builder_and_cache() -> None:
    symbol = "T" + uuid4().hex[:8].upper()

    with SessionLocal() as db:
        stock = Stock(
            symbol=symbol,
            name="Context Test Stock",
            exchange="TEST",
            industry="Testing",
        )

        db.add(stock)
        db.commit()
        db.refresh(stock)

        try:
            start = datetime(
                2026,
                9,
                1,
                12,
                0,
                tzinfo=timezone.utc,
            )

            for index in range(6):
                db.add(
                    Price(
                        stock_id=stock.id,
                        timestamp=(start + timedelta(days=index)),
                        close=Decimal(str(100 + index)),
                        volume=(1000 + index),
                        source="test",
                    )
                )

            db.add(
                Financial(
                    stock_id=stock.id,
                    period_end=date(
                        2025,
                        12,
                        31,
                    ),
                    period_type="annual",
                    revenue=Decimal(1000000),
                    net_income=Decimal(100000),
                    eps=Decimal("5.0"),
                    roe=Decimal("0.2"),
                    operating_cash_flow=(Decimal(120000)),
                    source="test",
                )
            )

            db.add(
                Announcement(
                    stock_id=stock.id,
                    title=("Test announcement"),
                    content=("Announcement content"),
                    source="test",
                    source_url=("https://example.test/announcement"),
                    published_at=start,
                )
            )

            db.add(
                News(
                    stock_id=stock.id,
                    title="Test news",
                    content="News content",
                    source="test",
                    source_url=("https://example.test/news"),
                    published_at=(start + timedelta(days=1)),
                )
            )

            db.commit()

            cache = FakeCache()

            builder = ContextBuilder(cache=cache)

            first = builder.build(
                db,
                symbol,
            )

            assert builder.last_cache_hit is False

            assert first.symbol == symbol

            assert first.market.latest_close == 105.0

            assert first.market.previous_close == 104.0

            assert first.market.five_day_return_pct == 5.0

            assert len(first.financials) == 1

            assert len(first.texts) == 2

            assert first.texts[0].source_ref.source_id

            assert first.texts[0].source_ref.time

            second = builder.build(
                db,
                symbol,
            )

            assert builder.last_cache_hit is True

            assert second.model_dump() == first.model_dump()

        finally:
            db.delete(stock)
            db.commit()
