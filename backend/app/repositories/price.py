from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.price import Price


def list_prices_for_stock(
    db: Session,
    stock_id: int,
    *,
    limit: int,
) -> list[Price]:
    statement = (
        select(Price)
        .where(
            Price.stock_id == stock_id,
        )
        .order_by(
            Price.timestamp.desc(),
            Price.id.desc(),
        )
        .limit(limit)
    )

    prices = list(db.scalars(statement))

    prices.reverse()

    return prices
