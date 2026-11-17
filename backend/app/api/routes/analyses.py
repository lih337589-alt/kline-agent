from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.report import (
    AnalysisCreatedResponse,
    AnalysisRequest,
)
from app.services.analysis import (
    AnalysisFailedError,
    StockNotFoundError,
    run_analysis,
)

router = APIRouter(
    prefix="/api/analyses",
    tags=["analyses"],
)


DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]


@router.post(
    "",
    response_model=AnalysisCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_analysis(
    payload: AnalysisRequest,
    db: DatabaseSession,
) -> AnalysisCreatedResponse:
    try:
        result = run_analysis(
            db,
            symbol=payload.symbol,
            use_cache=payload.use_cache,
        )

    except StockNotFoundError as exc:
        raise HTTPException(
            status_code=(status.HTTP_404_NOT_FOUND),
            detail=str(exc),
        ) from exc

    except AnalysisFailedError as exc:
        raise HTTPException(
            status_code=(status.HTTP_502_BAD_GATEWAY),
            detail=str(exc),
        ) from exc

    return AnalysisCreatedResponse(
        report_id=result.report.id,
        trace_id=result.trace_id,
        symbol=result.symbol,
        status=result.report.status,
    )
