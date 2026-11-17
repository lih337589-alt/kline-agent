from datetime import (
    datetime,
    timezone,
)

from fastapi.testclient import TestClient

from app.api.routes import stocks as stocks_route
from app.main import app
from app.schemas.price import (
    PriceRead,
    StockPriceSeries,
)

client = TestClient(app)


def _price_series() -> StockPriceSeries:
    first_timestamp = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    second_timestamp = datetime(
        2026,
        1,
        2,
        tzinfo=timezone.utc,
    )

    created_at = datetime(
        2026,
        1,
        3,
        tzinfo=timezone.utc,
    )

    return StockPriceSeries(
        symbol="AAPL",
        count=2,
        latest_timestamp=(second_timestamp),
        sources=["test"],
        prices=[
            PriceRead(
                id=1,
                timestamp=first_timestamp,
                open=99.0,
                high=101.0,
                low=98.0,
                close=100.0,
                volume=1000,
                source="test",
                created_at=created_at,
            ),
            PriceRead(
                id=2,
                timestamp=second_timestamp,
                open=100.0,
                high=102.0,
                low=99.0,
                close=101.0,
                volume=1100,
                source="test",
                created_at=created_at,
            ),
        ],
    )


def test_get_stock_prices_success(
    monkeypatch,
) -> None:
    received: dict[
        str,
        object,
    ] = {}

    def fake_get_stock_price_series(
        _db,
        symbol: str,
        *,
        limit: int,
    ):
        received["symbol"] = symbol
        received["limit"] = limit

        return _price_series()

    monkeypatch.setattr(
        stocks_route.price_service,
        "get_stock_price_series",
        fake_get_stock_price_series,
    )

    response = client.get("/api/stocks/AAPL/prices?limit=2")

    assert response.status_code == 200

    data = response.json()

    assert data["symbol"] == "AAPL"
    assert data["count"] == 2

    assert data["sources"] == ["test"]

    assert len(data["prices"]) == 2

    assert data["prices"][0]["close"] == 100.0

    assert data["prices"][1]["close"] == 101.0

    assert received == {
        "symbol": "AAPL",
        "limit": 2,
    }


def test_get_stock_prices_not_found(
    monkeypatch,
) -> None:
    def fake_get_stock_price_series(
        _db,
        symbol: str,
        *,
        limit: int,
    ):
        del symbol
        del limit

    monkeypatch.setattr(
        stocks_route.price_service,
        "get_stock_price_series",
        fake_get_stock_price_series,
    )

    response = client.get("/api/stocks/ZZZZ/prices")

    assert response.status_code == 404

    data = response.json()

    assert data["error"]["code"] == "http_error"

    assert data["error"]["path"] == "/api/stocks/ZZZZ/prices"


def test_get_stock_prices_rejects_invalid_limit() -> None:
    response = client.get("/api/stocks/AAPL/prices?limit=0")

    assert response.status_code == 422
