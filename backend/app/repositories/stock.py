from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.stock import Stock


def list_stocks(db: Session) -> list[Stock]:
    statement = select(Stock).order_by(Stock.symbol)

    return list(db.scalars(statement).all())


def get_stock_by_symbol(
    db: Session,
    symbol: str,
) -> Stock | None:
    statement = select(Stock).where(Stock.symbol == symbol)

    return db.scalar(statement)
