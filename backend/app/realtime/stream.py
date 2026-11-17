import asyncio
import random
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


class MarketTick(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    type: str = "market_tick"

    symbol: str = Field(
        min_length=1,
        max_length=32,
    )

    price: float = Field(
        gt=0.0,
    )

    volume: int = Field(
        ge=0,
    )

    timestamp: datetime


class SimulatedMarketStream:
    def __init__(
        self,
        symbol: str,
        *,
        initial_price: float = 320.0,
        interval_seconds: float = 1.0,
        random_generator: random.Random | None = None,
    ) -> None:
        normalized_symbol = symbol.strip().upper()

        if not normalized_symbol:
            raise ValueError("symbol must not be empty")

        if initial_price <= 0:
            raise ValueError("initial_price must be positive")

        if interval_seconds < 0:
            raise ValueError("interval_seconds must be non-negative")

        self.symbol = normalized_symbol

        self.current_price = initial_price

        self.interval_seconds = interval_seconds

        self.random = random_generator or random.Random()

    async def next_tick(
        self,
    ) -> MarketTick:
        if self.interval_seconds > 0:
            await asyncio.sleep(self.interval_seconds)

        percentage_change = self.random.uniform(
            -0.004,
            0.004,
        )

        next_price = self.current_price * (1.0 + percentage_change)

        self.current_price = max(
            0.01,
            round(
                next_price,
                2,
            ),
        )

        volume = self.random.randint(
            1_000,
            50_000,
        )

        return MarketTick(
            symbol=self.symbol,
            price=self.current_price,
            volume=volume,
            timestamp=datetime.now(
                timezone.utc,
            ),
        )
