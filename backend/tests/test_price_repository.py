from datetime import (
    datetime,
    timedelta,
    timezone,
)
from decimal import Decimal
from uuid import uuid4

from app.database.session import SessionLocal
from app.models.price import Price
from app.models.stock import Stock
from app.repositories.price import (
    list_prices_for_stock,
)


def test_list_prices_returns_latest_in_chronological_order() -> None:
    symbol = "P" + uuid4().hex[:8].upper()

    with SessionLocal() as db:
        stock = Stock(
            symbol=symbol,
            name="Price Repository Test Stock",
            exchange="TEST",
            industry="Testing",
        )

        db.add(stock)
        db.commit()
        db.refresh(stock)

        try:
            start = datetime(
                2026,
                1,
                1,
                tzinfo=timezone.utc,
            )

            for index in range(3):
                value = Decimal(str(100 + index))

                db.add(
                    Price(
                        stock_id=stock.id,
                        timestamp=(start + timedelta(days=index)),
                        open=value,
                        high=(value + Decimal(1)),
                        low=(value - Decimal(1)),
                        close=value,
                        volume=(1000 + index),
                        source="test",
                    )
                )

            db.commit()

            prices = list_prices_for_stock(
                db,
                stock.id,
                limit=2,
            )

            assert len(prices) == 2

            assert prices[0].close == Decimal(101)

            assert prices[1].close == Decimal(102)

            assert prices[0].timestamp < prices[1].timestamp

        finally:
            db.delete(stock)
            db.commit()
