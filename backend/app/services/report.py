from sqlalchemy.orm import Session

from app.repositories.report import (
    get_report_by_id,
)
from app.repositories.stock import (
    get_stock_by_symbol,
)
from app.schemas.report import (
    ReportPayload,
    ReportRead,
)


def read_report(
    db: Session,
    report_id: int,
) -> ReportRead | None:
    report = get_report_by_id(
        db,
        report_id,
    )

    if report is None:
        return None

    payload = ReportPayload.model_validate_json(report.report_json)

    stock = get_stock_by_symbol(
        db,
        payload.symbol,
    )

    if stock is None:
        return None

    return ReportRead(
        id=report.id,
        stock_id=report.stock_id,
        symbol=payload.symbol,
        trace_id=report.trace_id,
        title=report.title,
        status=report.status,
        source=report.source,
        report=payload,
        created_at=report.created_at,
    )
