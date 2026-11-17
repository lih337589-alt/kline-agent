from sqlalchemy.orm import Session

from app.models.stock import Stock
from app.repositories import stock as stock_repository


def list_stocks(db: Session) -> list[Stock]:
    return stock_repository.list_stocks(db)


def get_stock_by_symbol(
    db: Session,
    symbol: str,
) -> Stock | None:
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        return None

    return stock_repository.get_stock_by_symbol(
        db,
        normalized_symbol,
    )
