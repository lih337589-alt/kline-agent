from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StockRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    symbol: str
    name: str
    exchange: str | None
    industry: str | None
    created_at: datetime
