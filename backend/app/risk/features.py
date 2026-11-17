from collections import deque
from datetime import timedelta

from app.realtime.stream import MarketTick
from app.schemas.risk import FeatureSnapshot


class RiskFeatureEngine:
    def __init__(
        self,
        *,
        window_seconds: int = 60,
    ) -> None:
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")

        self.window_seconds = window_seconds

        self._history: dict[
            str,
            deque[MarketTick],
        ] = {}

    def update(
        self,
        tick: MarketTick,
    ) -> FeatureSnapshot:
        symbol = tick.symbol.strip().upper()

        history = self._history.setdefault(
            symbol,
            deque(),
        )

        previous_tick = history[-1] if history else None

        cutoff = tick.timestamp - timedelta(seconds=self.window_seconds)

        while history and history[0].timestamp < cutoff:
            history.popleft()

        reference_tick = history[0] if history else None

        return_1m = None

        if reference_tick is not None and reference_tick.price > 0:
            return_1m = (tick.price - reference_tick.price) / reference_tick.price

        price_jump_pct = None

        if previous_tick is not None and previous_tick.price > 0:
            price_jump_pct = (tick.price - previous_tick.price) / previous_tick.price

        volume_ratio = None

        if history:
            average_volume = sum(item.volume for item in history) / len(history)

            if average_volume > 0:
                volume_ratio = tick.volume / average_volume

        history.append(tick)

        return FeatureSnapshot(
            symbol=symbol,
            timestamp=tick.timestamp,
            price=tick.price,
            volume=tick.volume,
            return_1m=return_1m,
            price_jump_pct=(price_jump_pct),
            volume_ratio=volume_ratio,
            sample_count=len(history),
        )
