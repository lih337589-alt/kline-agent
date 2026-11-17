from datetime import (
    datetime,
    timezone,
)
from uuid import uuid4

from fastapi.testclient import (
    TestClient,
)

from app.database.session import (
    SessionLocal,
)
from app.main import app
from app.models.stock import Stock
from app.repositories.risk_alert import (
    create_risk_alert,
    set_risk_alert_explanation,
)
from app.schemas.risk import (
    RiskExplanation,
)

client = TestClient(app)


NOW = datetime(
    2026,
    9,
    22,
    12,
    0,
    tzinfo=timezone.utc,
)


def test_alerts_api_returns_explanation() -> None:
    symbol = "X" + uuid4().hex[:8].upper()

    with SessionLocal() as db:
        stock = Stock(
            symbol=symbol,
            name=("Alert Explanation API Test"),
            exchange="TEST",
            industry="Testing",
        )

        db.add(stock)
        db.commit()
        db.refresh(stock)

        stock_id = stock.id

        try:
            alert = create_risk_alert(
                db,
                stock_id=stock.id,
                alert_type="price_drop",
                severity="high",
                message="Test alert.",
                source=("risk_rule_engine"),
                event_time=NOW,
            )

            explanation = RiskExplanation(
                severity="high",
                reason="Test reason.",
                impact_path=["Test path"],
                uncertainty=("Test uncertainty."),
                suggested_attention=["Review the signal"],
            )

            set_risk_alert_explanation(
                db,
                alert_id=alert.id,
                explanation_json=(explanation.model_dump_json()),
            )

            db.commit()

            response = client.get(
                "/api/alerts",
                params={
                    "symbol": symbol,
                },
            )

            assert response.status_code == 200

            payload = response.json()

            assert payload["count"] == 1

            result = payload["alerts"][0]

            assert result["explanation"]["severity"] == "high"

            assert result["explanation"]["reason"] == "Test reason."

        finally:
            stock = db.get(
                Stock,
                stock_id,
            )

            if stock is not None:
                db.delete(stock)
                db.commit()
