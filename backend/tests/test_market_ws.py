from datetime import (
    datetime,
    timezone,
)

from fastapi.testclient import (
    TestClient,
)

from app.api.routes import (
    ws as ws_route,
)
from app.main import app
from app.realtime.stream import (
    MarketTick,
)

client = TestClient(app)


class FakeMarketStream:
    def __init__(
        self,
        symbol: str,
    ) -> None:
        self.symbol = symbol
        self.counter = 0

    async def next_tick(
        self,
    ) -> MarketTick:
        self.counter += 1

        return MarketTick(
            symbol=self.symbol,
            price=(320.0 + self.counter),
            volume=(10_000 + self.counter),
            timestamp=datetime.now(
                timezone.utc,
            ),
        )


def test_market_websocket_sends_continuous_ticks(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        ws_route,
        "SimulatedMarketStream",
        FakeMarketStream,
    )

    with client.websocket_connect("/ws/market?symbol=aapl") as websocket:
        first = websocket.receive_json()

        second = websocket.receive_json()

    assert first["type"] == ("market_tick")

    assert first["symbol"] == ("AAPL")

    assert second["symbol"] == ("AAPL")

    assert second["price"] > first["price"]

    assert second["volume"] > first["volume"]


def test_market_websocket_defaults_to_aapl(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        ws_route,
        "SimulatedMarketStream",
        FakeMarketStream,
    )

    with client.websocket_connect("/ws/market") as websocket:
        tick = websocket.receive_json()

    assert tick["symbol"] == ("AAPL")
