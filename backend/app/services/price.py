from sqlalchemy.orm import Session

from app.repositories.price import (
    list_prices_for_stock,
)
from app.repositories.stock import (
    get_stock_by_symbol,
)
from app.schemas.price import (
    PriceRead,
    StockPriceSeries,
)


def get_stock_price_series(
    db: Session,
    symbol: str,
    *,
    limit: int,
) -> StockPriceSeries | None:
    stock = get_stock_by_symbol(
        db,
        symbol,
    )

    if stock is None:
        return None

    price_models = list_prices_for_stock(
        db,
        stock.id,
        limit=limit,
    )

    prices = [PriceRead.model_validate(price) for price in price_models]

    latest_timestamp = prices[-1].timestamp if prices else None

    sources = sorted({price.source for price in prices})

    return StockPriceSeries(
        symbol=stock.symbol,
        count=len(prices),
        latest_timestamp=latest_timestamp,
        sources=sources,
        prices=prices,
    )
