from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.risk_alert import (
    list_risk_alerts,
)
from app.schemas.risk import (
    RiskAlertListResponse,
    RiskAlertRead,
    RiskExplanation,
    RiskSeverity,
)

router = APIRouter(
    prefix="/api/alerts",
    tags=["alerts"],
)


def _parse_explanation(
    value: str | None,
) -> RiskExplanation | None:
    if not value:
        return None

    try:
        return RiskExplanation.model_validate_json(value)

    except ValidationError:
        return None


@router.get(
    "",
    response_model=(RiskAlertListResponse),
)
def get_alerts(
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    symbol: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=32,
        ),
    ] = None,
    severity: Annotated[
        RiskSeverity | None,
        Query(),
    ] = None,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
        ),
    ] = 20,
) -> RiskAlertListResponse:
    normalized_symbol = symbol.strip().upper() if symbol is not None else None

    rows = list_risk_alerts(
        db,
        symbol=normalized_symbol,
        severity=severity,
        limit=limit,
    )

    alerts = [
        RiskAlertRead(
            id=alert.id,
            stock_id=alert.stock_id,
            symbol=stock_symbol,
            alert_type=(alert.alert_type),
            severity=(alert.severity),
            message=alert.message,
            source=alert.source,
            event_time=(alert.event_time),
            created_at=(alert.created_at),
            explanation=(_parse_explanation(alert.explanation_json)),
        )
        for (
            alert,
            stock_symbol,
        ) in rows
    ]

    return RiskAlertListResponse(
        count=len(alerts),
        alerts=alerts,
    )
