from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.risk_alert import RiskAlert
from app.models.stock import Stock


def create_risk_alert(
    db: Session,
    *,
    stock_id: int,
    alert_type: str,
    severity: str,
    message: str,
    source: str,
    event_time: datetime,
) -> RiskAlert:
    alert = RiskAlert(
        stock_id=stock_id,
        alert_type=alert_type,
        severity=severity,
        message=message,
        source=source,
        event_time=event_time,
    )

    db.add(alert)
    db.flush()

    return alert


def get_latest_risk_alert(
    db: Session,
    *,
    stock_id: int,
    alert_type: str,
) -> RiskAlert | None:
    statement = (
        select(RiskAlert)
        .where(
            RiskAlert.stock_id == stock_id,
            RiskAlert.alert_type == alert_type,
        )
        .order_by(RiskAlert.event_time.desc())
        .limit(1)
    )

    return db.scalar(statement)


def set_risk_alert_explanation(
    db: Session,
    *,
    alert_id: int,
    explanation_json: str,
) -> RiskAlert | None:
    alert = db.get(
        RiskAlert,
        alert_id,
    )

    if alert is None:
        return None

    alert.explanation_json = explanation_json

    db.flush()

    return alert


def list_risk_alerts(
    db: Session,
    *,
    symbol: str | None = None,
    severity: str | None = None,
    limit: int = 20,
) -> list[
    tuple[
        RiskAlert,
        str,
    ]
]:
    statement = select(
        RiskAlert,
        Stock.symbol,
    ).join(
        Stock,
        Stock.id == RiskAlert.stock_id,
    )

    if symbol is not None:
        statement = statement.where(Stock.symbol == symbol)

    if severity is not None:
        statement = statement.where(RiskAlert.severity == severity)

    statement = statement.order_by(
        RiskAlert.event_time.desc(),
        RiskAlert.id.desc(),
    ).limit(limit)

    rows = db.execute(statement).all()

    return [
        (
            row[0],
            row[1],
        )
        for row in rows
    ]
