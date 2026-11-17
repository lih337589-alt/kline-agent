from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PriceRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    timestamp: datetime
    open: float | None
    high: float | None
    low: float | None
    close: float
    volume: int | None
    source: str
    created_at: datetime


class StockPriceSeries(BaseModel):
    symbol: str
    count: int
    latest_timestamp: datetime | None
    sources: list[str]
    prices: list[PriceRead]
