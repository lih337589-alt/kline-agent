from datetime import (
    datetime,
    timedelta,
    timezone,
)

import pytest

from app.realtime.stream import (
    MarketTick,
)
from app.risk.features import (
    RiskFeatureEngine,
)

BASE_TIME = datetime(
    2026,
    9,
    21,
    12,
    0,
    0,
    tzinfo=timezone.utc,
)


def make_tick(
    *,
    seconds: int,
    price: float,
    volume: int,
    symbol: str = "AAPL",
) -> MarketTick:
    return MarketTick(
        symbol=symbol,
        price=price,
        volume=volume,
        timestamp=(BASE_TIME + timedelta(seconds=seconds)),
    )


def test_first_tick_has_no_derived_features() -> None:
    engine = RiskFeatureEngine(
        window_seconds=60,
    )

    snapshot = engine.update(
        make_tick(
            seconds=0,
            price=100.0,
            volume=1_000,
        )
    )

    assert snapshot.return_1m is None

    assert snapshot.price_jump_pct is None

    assert snapshot.volume_ratio is None

    assert snapshot.sample_count == 1


def test_feature_engine_calculates_returns_and_volume_ratio() -> None:
    engine = RiskFeatureEngine(
        window_seconds=60,
    )

    engine.update(
        make_tick(
            seconds=0,
            price=100.0,
            volume=1_000,
        )
    )

    snapshot = engine.update(
        make_tick(
            seconds=30,
            price=102.0,
            volume=2_000,
        )
    )

    assert snapshot.return_1m == pytest.approx(0.02)

    assert snapshot.price_jump_pct == pytest.approx(0.02)

    assert snapshot.volume_ratio == pytest.approx(2.0)

    assert snapshot.sample_count == 2


def test_feature_engine_uses_window_reference_tick() -> None:
    engine = RiskFeatureEngine(
        window_seconds=60,
    )

    engine.update(
        make_tick(
            seconds=0,
            price=100.0,
            volume=1_000,
        )
    )

    engine.update(
        make_tick(
            seconds=30,
            price=101.0,
            volume=1_000,
        )
    )

    snapshot = engine.update(
        make_tick(
            seconds=60,
            price=98.0,
            volume=1_000,
        )
    )

    assert snapshot.return_1m == pytest.approx(-0.02)

    assert snapshot.price_jump_pct == pytest.approx((98.0 - 101.0) / 101.0)


def test_feature_engine_discards_old_ticks() -> None:
    engine = RiskFeatureEngine(
        window_seconds=60,
    )

    engine.update(
        make_tick(
            seconds=0,
            price=100.0,
            volume=1_000,
        )
    )

    engine.update(
        make_tick(
            seconds=30,
            price=101.0,
            volume=1_000,
        )
    )

    snapshot = engine.update(
        make_tick(
            seconds=91,
            price=102.0,
            volume=1_000,
        )
    )

    assert snapshot.return_1m is None

    assert snapshot.sample_count == 1


def test_feature_engine_keeps_symbols_independent() -> None:
    engine = RiskFeatureEngine(
        window_seconds=60,
    )

    engine.update(
        make_tick(
            seconds=0,
            price=100.0,
            volume=1_000,
            symbol="AAPL",
        )
    )

    snapshot = engine.update(
        make_tick(
            seconds=10,
            price=200.0,
            volume=2_000,
            symbol="MSFT",
        )
    )

    assert snapshot.symbol == "MSFT"

    assert snapshot.return_1m is None

    assert snapshot.sample_count == 1
