from datetime import (
    datetime,
    timedelta,
    timezone,
)
from uuid import uuid4

from app.database.session import (
    SessionLocal,
)
from app.models.stock import Stock
from app.repositories.risk_alert import (
    get_latest_risk_alert,
)
from app.risk.alerts import (
    persist_rule_hits,
)
from app.schemas.risk import (
    FeatureSnapshot,
    RuleHit,
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


def make_snapshot(
    *,
    timestamp: datetime,
) -> FeatureSnapshot:
    return FeatureSnapshot(
        symbol="TEST",
        timestamp=timestamp,
        price=100.0,
        volume=1_000,
        return_1m=-0.03,
        price_jump_pct=-0.02,
        volume_ratio=3.0,
        sample_count=2,
    )


def make_hit(
    rule_name: str = "price_drop",
) -> RuleHit:
    return RuleHit(
        rule_name=rule_name,
        severity="high",
        message="Test risk rule hit.",
        observed_value=-0.03,
        threshold=-0.02,
    )


def test_persist_rule_hits_respects_cooldown() -> None:
    symbol = "R" + uuid4().hex[:8].upper()

    with SessionLocal() as db:
        stock = Stock(
            symbol=symbol,
            name="Risk Test Stock",
            exchange="TEST",
            industry="Testing",
        )

        db.add(stock)
        db.commit()
        db.refresh(stock)

        try:
            first = persist_rule_hits(
                db,
                stock_id=stock.id,
                snapshot=make_snapshot(
                    timestamp=BASE_TIME,
                ),
                rule_hits=[make_hit()],
                cooldown_seconds=60,
            )

            db.commit()

            assert len(first) == 1

            duplicate = persist_rule_hits(
                db,
                stock_id=stock.id,
                snapshot=make_snapshot(
                    timestamp=(BASE_TIME + timedelta(seconds=30)),
                ),
                rule_hits=[make_hit()],
                cooldown_seconds=60,
            )

            db.commit()

            assert duplicate == []

            after_cooldown = persist_rule_hits(
                db,
                stock_id=stock.id,
                snapshot=make_snapshot(
                    timestamp=(BASE_TIME + timedelta(seconds=61)),
                ),
                rule_hits=[make_hit()],
                cooldown_seconds=60,
            )

            db.commit()

            assert len(after_cooldown) == 1

            latest = get_latest_risk_alert(
                db,
                stock_id=stock.id,
                alert_type=("price_drop"),
            )

            assert latest is not None

            assert latest.event_time == (BASE_TIME + timedelta(seconds=61))

        finally:
            db.delete(stock)
            db.commit()


def test_cooldown_is_independent_per_rule() -> None:
    symbol = "R" + uuid4().hex[:8].upper()

    with SessionLocal() as db:
        stock = Stock(
            symbol=symbol,
            name="Risk Test Stock",
            exchange="TEST",
            industry="Testing",
        )

        db.add(stock)
        db.commit()
        db.refresh(stock)

        try:
            created = persist_rule_hits(
                db,
                stock_id=stock.id,
                snapshot=make_snapshot(
                    timestamp=BASE_TIME,
                ),
                rule_hits=[
                    make_hit("price_drop"),
                    make_hit("price_jump"),
                ],
                cooldown_seconds=60,
            )

            db.commit()

            assert len(created) == 2

            assert {item.alert_type for item in created} == {
                "price_drop",
                "price_jump",
            }

        finally:
            db.delete(stock)
            db.commit()
