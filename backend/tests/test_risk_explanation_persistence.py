from datetime import (
    datetime,
    timezone,
)
from uuid import uuid4

from app.api.routes import (
    ws as ws_route,
)
from app.database.session import (
    SessionLocal,
)
from app.llm.client import (
    LLMCallInfo,
)
from app.models.risk_alert import (
    RiskAlert,
)
from app.models.stock import Stock
from app.repositories.risk_alert import (
    create_risk_alert,
)
from app.schemas.risk import (
    FeatureSnapshot,
    RiskExplanation,
    RuleHit,
)

NOW = datetime(
    2026,
    9,
    22,
    12,
    0,
    tzinfo=timezone.utc,
)


class FakeLLMClient:
    def generate_structured(
        self,
        **kwargs: object,
    ) -> tuple[
        RiskExplanation,
        LLMCallInfo,
    ]:
        return (
            RiskExplanation(
                severity="high",
                reason=("A deterministic threshold was crossed."),
                impact_path=[
                    "Rapid price move",
                    "Higher short-term volatility",
                ],
                uncertainty=("The supplied evidence does not establish a cause."),
                suggested_attention=[
                    "Monitor whether the move persists",
                ],
            ),
            LLMCallInfo(
                model="fake-model",
                elapsed_ms=1,
                total_tokens=20,
            ),
        )


def test_risk_explanation_is_persisted(
    monkeypatch,
) -> None:
    symbol = "E" + uuid4().hex[:8].upper()

    with SessionLocal() as db:
        stock = Stock(
            symbol=symbol,
            name=("Explanation Test Stock"),
            exchange="TEST",
            industry="Testing",
        )

        db.add(stock)
        db.commit()
        db.refresh(stock)

        stock_id = stock.id

        alert = create_risk_alert(
            db,
            stock_id=stock.id,
            alert_type="price_drop",
            severity="high",
            message=("Test price drop alert."),
            source=("risk_rule_engine"),
            event_time=NOW,
        )

        alert_id = alert.id

        db.commit()

    monkeypatch.setattr(
        ws_route,
        "_make_llm_client",
        lambda: FakeLLMClient(),
    )

    try:
        ws_route._explain_and_store_alert(
            alert_id=alert_id,
            symbol=symbol,
            snapshot=FeatureSnapshot(
                symbol=symbol,
                timestamp=NOW,
                price=97.0,
                volume=1_000,
                return_1m=-0.03,
                price_jump_pct=-0.03,
                volume_ratio=1.0,
                sample_count=2,
            ),
            rule_hit=RuleHit(
                rule_name="price_drop",
                severity="high",
                message=("Test price drop alert."),
                observed_value=-0.03,
                threshold=-0.02,
            ),
        )

        with SessionLocal() as db:
            alert = db.get(
                RiskAlert,
                alert_id,
            )

            assert alert is not None

            assert alert.explanation_json is not None

            explanation = RiskExplanation.model_validate_json(alert.explanation_json)

            assert explanation.severity == "high"

            assert explanation.reason == ("A deterministic threshold was crossed.")

    finally:
        with SessionLocal() as db:
            stock = db.get(
                Stock,
                stock_id,
            )

            if stock is not None:
                db.delete(stock)
                db.commit()
