from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.report import Report


def create_report(
    db: Session,
    *,
    stock_id: int,
    trace_id: str,
    title: str,
    report_json: str,
    status: str,
    source: str,
) -> Report:
    report = Report(
        stock_id=stock_id,
        trace_id=trace_id,
        title=title,
        report_json=report_json,
        status=status,
        source=source,
    )

    db.add(report)
    db.flush()

    return report


def get_report_by_id(
    db: Session,
    report_id: int,
) -> Report | None:
    statement = select(Report).where(Report.id == report_id)

    return db.scalar(statement)
