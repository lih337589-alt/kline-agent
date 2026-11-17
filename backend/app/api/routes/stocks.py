from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.price import StockPriceSeries
from app.schemas.stock import StockRead
from app.services import price as price_service
from app.services import stock as stock_service

router = APIRouter(
    prefix="/api/stocks",
    tags=["stocks"],
)


DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]


PriceLimit = Annotated[
    int,
    Query(
        ge=1,
        le=500,
    ),
]


@router.get(
    "",
    response_model=list[StockRead],
)
def read_stocks(
    db: DatabaseSession,
) -> list[StockRead]:
    return stock_service.list_stocks(db)


@router.get(
    "/{symbol}/prices",
    response_model=StockPriceSeries,
)
def read_stock_prices(
    symbol: str,
    db: DatabaseSession,
    limit: PriceLimit = 120,
) -> StockPriceSeries:
    price_series = price_service.get_stock_price_series(
        db,
        symbol,
        limit=limit,
    )

    if price_series is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(f"Stock '{symbol.upper()}' not found"),
        )

    return price_series


@router.get(
    "/{symbol}",
    response_model=StockRead,
)
def read_stock(
    symbol: str,
    db: DatabaseSession,
) -> StockRead:
    stock = stock_service.get_stock_by_symbol(
        db,
        symbol,
    )

    if stock is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(f"Stock '{symbol.upper()}' not found"),
        )

    return stock
