from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.routes import (
    analyses as analyses_route,
)
from app.main import app
from app.services.analysis import (
    AnalysisFailedError,
    StockNotFoundError,
)

client = TestClient(app)


def test_create_analysis_success(
    monkeypatch,
) -> None:
    received: dict[
        str,
        object,
    ] = {}

    def fake_run_analysis(
        _db,
        *,
        symbol: str,
        use_cache: bool,
    ):
        received["symbol"] = symbol
        received["use_cache"] = use_cache

        return SimpleNamespace(
            report=SimpleNamespace(
                id=123,
                status="completed",
            ),
            trace_id="trace-api-test",
            symbol="AAPL",
        )

    monkeypatch.setattr(
        analyses_route,
        "run_analysis",
        fake_run_analysis,
    )

    response = client.post(
        "/api/analyses",
        json={
            "symbol": "aapl",
            "use_cache": False,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data == {
        "report_id": 123,
        "trace_id": "trace-api-test",
        "symbol": "AAPL",
        "status": "completed",
    }

    assert received == {
        "symbol": "aapl",
        "use_cache": False,
    }


def test_create_analysis_stock_not_found(
    monkeypatch,
) -> None:
    def fake_run_analysis(
        _db,
        *,
        symbol: str,
        use_cache: bool,
    ):
        del use_cache

        raise StockNotFoundError(f"Stock '{symbol.upper()}' not found")

    monkeypatch.setattr(
        analyses_route,
        "run_analysis",
        fake_run_analysis,
    )

    response = client.post(
        "/api/analyses",
        json={
            "symbol": "missing",
            "use_cache": False,
        },
    )

    assert response.status_code == 404

    data = response.json()

    assert data["error"]["code"] == "http_error"

    assert data["error"]["path"] == "/api/analyses"


def test_create_analysis_workflow_failure(
    monkeypatch,
) -> None:
    def fake_run_analysis(
        _db,
        *,
        symbol: str,
        use_cache: bool,
    ):
        del symbol
        del use_cache

        raise AnalysisFailedError("judge: simulated failure")

    monkeypatch.setattr(
        analyses_route,
        "run_analysis",
        fake_run_analysis,
    )

    response = client.post(
        "/api/analyses",
        json={
            "symbol": "AAPL",
            "use_cache": True,
        },
    )

    assert response.status_code == 502

    data = response.json()

    assert data["error"]["code"] == "http_error"

    assert data["error"]["path"] == "/api/analyses"


def test_create_analysis_validation_error() -> None:
    response = client.post(
        "/api/analyses",
        json={
            "use_cache": True,
        },
    )

    assert response.status_code == 422
