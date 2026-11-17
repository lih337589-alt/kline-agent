from datetime import (
    datetime,
    timedelta,
    timezone,
)
from uuid import uuid4

from fastapi.testclient import TestClient

from app.database.session import SessionLocal
from app.main import app
from app.models.stock import Stock
from app.repositories.risk_alert import (
    create_risk_alert,
)

client = TestClient(app)


BASE_TIME = datetime(
    2026,
    9,
    21,
    12,
    0,
    tzinfo=timezone.utc,
)


def test_list_alerts_filters_symbol_and_orders_latest_first() -> None:
    symbol = "A" + uuid4().hex[:8].upper()

    with SessionLocal() as db:
        stock = Stock(
            symbol=symbol,
            name="Alerts API Test",
            exchange="TEST",
            industry="Testing",
        )

        db.add(stock)
        db.commit()
        db.refresh(stock)

        stock_id = stock.id

        try:
            create_risk_alert(
                db,
                stock_id=stock.id,
                alert_type="volume_spike",
                severity="medium",
                message=("Volume spike test."),
                source="test",
                event_time=BASE_TIME,
            )

            create_risk_alert(
                db,
                stock_id=stock.id,
                alert_type="price_drop",
                severity="high",
                message=("Price drop test."),
                source="test",
                event_time=(BASE_TIME + timedelta(seconds=10)),
            )

            db.commit()

            response = client.get(
                "/api/alerts",
                params={
                    "symbol": symbol.lower(),
                    "limit": 20,
                },
            )

            assert response.status_code == 200

            payload = response.json()

            assert payload["count"] == 2

            assert [item["alert_type"] for item in payload["alerts"]] == [
                "price_drop",
                "volume_spike",
            ]

            assert all(item["symbol"] == symbol for item in payload["alerts"])

            assert all(item["explanation"] is None for item in payload["alerts"])

        finally:
            stock = db.get(
                Stock,
                stock_id,
            )

            if stock is not None:
                db.delete(stock)
                db.commit()


def test_list_alerts_filters_severity() -> None:
    symbol = "A" + uuid4().hex[:8].upper()

    with SessionLocal() as db:
        stock = Stock(
            symbol=symbol,
            name=("Alerts Severity Test"),
            exchange="TEST",
            industry="Testing",
        )

        db.add(stock)
        db.commit()
        db.refresh(stock)

        stock_id = stock.id

        try:
            create_risk_alert(
                db,
                stock_id=stock.id,
                alert_type="price_drop",
                severity="high",
                message="High alert.",
                source="test",
                event_time=BASE_TIME,
            )

            create_risk_alert(
                db,
                stock_id=stock.id,
                alert_type=("volume_spike"),
                severity="medium",
                message="Medium alert.",
                source="test",
                event_time=(BASE_TIME + timedelta(seconds=1)),
            )

            db.commit()

            response = client.get(
                "/api/alerts",
                params={
                    "symbol": symbol,
                    "severity": "high",
                },
            )

            assert response.status_code == 200

            payload = response.json()

            assert payload["count"] == 1

            assert payload["alerts"][0]["severity"] == "high"

            assert payload["alerts"][0]["alert_type"] == "price_drop"

        finally:
            stock = db.get(
                Stock,
                stock_id,
            )

            if stock is not None:
                db.delete(stock)
                db.commit()


def test_list_alerts_rejects_invalid_limit() -> None:
    response = client.get(
        "/api/alerts",
        params={
            "limit": 0,
        },
    )

    assert response.status_code == 422
