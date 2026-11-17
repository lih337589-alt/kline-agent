from datetime import (
    datetime,
    timedelta,
    timezone,
)
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.routes import ws as ws_route
from app.database.session import SessionLocal
from app.main import app
from app.models.risk_alert import RiskAlert
from app.models.stock import Stock
from app.realtime.stream import MarketTick

client = TestClient(app)


BASE_TIME = datetime(
    2026,
    9,
    21,
    12,
    0,
    0,
    tzinfo=timezone.utc,
)


class RiskTriggeringMarketStream:
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

        if self.counter == 1:
            price = 100.0
            seconds = 0
        else:
            price = 97.0
            seconds = 60

        return MarketTick(
            symbol=self.symbol,
            price=price,
            volume=1_000,
            timestamp=(BASE_TIME + timedelta(seconds=seconds)),
        )


def test_market_websocket_persists_risk_alerts(
    monkeypatch,
) -> None:
    symbol = "W" + uuid4().hex[:8].upper()

    with SessionLocal() as db:
        stock = Stock(
            symbol=symbol,
            name="WebSocket Risk Test",
            exchange="TEST",
            industry="Testing",
        )

        db.add(stock)
        db.commit()
        db.refresh(stock)

        stock_id = stock.id

    monkeypatch.setattr(
        ws_route,
        "SimulatedMarketStream",
        RiskTriggeringMarketStream,
    )

    try:
        with client.websocket_connect(f"/ws/market?symbol={symbol}") as websocket:
            first = websocket.receive_json()
            second = websocket.receive_json()

        assert first["price"] == 100.0
        assert second["price"] == 97.0

        with SessionLocal() as db:
            statement = (
                select(RiskAlert)
                .where(RiskAlert.stock_id == stock_id)
                .order_by(RiskAlert.id)
            )

            alerts = list(db.scalars(statement).all())

            assert {alert.alert_type for alert in alerts} == {
                "price_drop",
                "price_jump",
            }

            assert all(alert.source == "risk_rule_engine" for alert in alerts)

            assert all(
                alert.event_time == (BASE_TIME + timedelta(seconds=60))
                for alert in alerts
            )

    finally:
        with SessionLocal() as db:
            stock = db.get(
                Stock,
                stock_id,
            )

            if stock is not None:
                db.delete(stock)
                db.commit()
