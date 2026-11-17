from fastapi import APIRouter

from app.api.routes.alerts import router as alerts_router
from app.api.routes.analyses import router as analyses_router
from app.api.routes.reports import router as reports_router
from app.api.routes.stocks import router as stocks_router
from app.api.routes.ws import router as ws_router
from app.core.config import settings

api_router = APIRouter()

api_router.include_router(stocks_router)

api_router.include_router(analyses_router)

api_router.include_router(reports_router)

api_router.include_router(alerts_router)

api_router.include_router(ws_router)


@api_router.get(
    "/health",
    tags=["system"],
)
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "kline-agent-backend",
        "version": settings.app_version,
        "environment": settings.environment,
    }
