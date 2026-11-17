from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.risk_alert import RiskAlert
from app.repositories.risk_alert import (
    create_risk_alert,
    get_latest_risk_alert,
)
from app.schemas.risk import (
    FeatureSnapshot,
    RuleHit,
)


def should_create_alert(
    db: Session,
    *,
    stock_id: int,
    rule_hit: RuleHit,
    snapshot: FeatureSnapshot,
    cooldown_seconds: int = (settings.risk_alert_cooldown_seconds),
) -> bool:
    if cooldown_seconds < 0:
        raise ValueError("cooldown_seconds must be non-negative")

    latest = get_latest_risk_alert(
        db,
        stock_id=stock_id,
        alert_type=(rule_hit.rule_name),
    )

    if latest is None:
        return True

    cooldown_end = latest.event_time + timedelta(seconds=cooldown_seconds)

    return snapshot.timestamp >= cooldown_end


def persist_rule_hits(
    db: Session,
    *,
    stock_id: int,
    snapshot: FeatureSnapshot,
    rule_hits: list[RuleHit],
    cooldown_seconds: int = (settings.risk_alert_cooldown_seconds),
) -> list[RiskAlert]:
    created: list[RiskAlert] = []

    for hit in rule_hits:
        if not should_create_alert(
            db,
            stock_id=stock_id,
            rule_hit=hit,
            snapshot=snapshot,
            cooldown_seconds=(cooldown_seconds),
        ):
            continue

        alert = create_risk_alert(
            db,
            stock_id=stock_id,
            alert_type=(hit.rule_name),
            severity=hit.severity,
            message=hit.message,
            source="risk_rule_engine",
            event_time=(snapshot.timestamp),
        )

        created.append(alert)

    return created
