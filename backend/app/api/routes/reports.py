from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.report import ReportRead
from app.services.report import read_report

router = APIRouter(
    prefix="/api/reports",
    tags=["reports"],
)


DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]


@router.get(
    "/{report_id}",
    response_model=ReportRead,
)
def get_report(
    report_id: int,
    db: DatabaseSession,
) -> ReportRead:
    report = read_report(
        db,
        report_id,
    )

    if report is None:
        raise HTTPException(
            status_code=(status.HTTP_404_NOT_FOUND),
            detail=(f"Report {report_id} not found"),
        )

    return report
