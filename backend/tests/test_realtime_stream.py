import asyncio
import random

import pytest

from app.realtime.stream import (
    SimulatedMarketStream,
)


def test_simulated_market_stream_normalizes_symbol() -> None:
    stream = SimulatedMarketStream(
        " aapl ",
        interval_seconds=0,
    )

    assert stream.symbol == "AAPL"


def test_simulated_market_stream_rejects_empty_symbol() -> None:
    with pytest.raises(
        ValueError,
        match="symbol must not be empty",
    ):
        SimulatedMarketStream(
            "   ",
            interval_seconds=0,
        )


def test_simulated_market_stream_rejects_invalid_price() -> None:
    with pytest.raises(
        ValueError,
        match="initial_price must be positive",
    ):
        SimulatedMarketStream(
            "AAPL",
            initial_price=0,
            interval_seconds=0,
        )


def test_simulated_market_stream_generates_valid_tick() -> None:
    stream = SimulatedMarketStream(
        "AAPL",
        initial_price=320.0,
        interval_seconds=0,
        random_generator=random.Random(42),
    )

    tick = asyncio.run(stream.next_tick())

    assert tick.type == "market_tick"

    assert tick.symbol == "AAPL"

    assert tick.price > 0

    assert 1_000 <= tick.volume <= 50_000

    assert tick.timestamp.tzinfo is not None
