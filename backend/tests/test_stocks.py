from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_stocks() -> None:
    response = client.get("/api/stocks")

    assert response.status_code == 200

    data = response.json()

    symbols = {stock["symbol"] for stock in data}

    assert "AAPL" in symbols
    assert "MSFT" in symbols
    assert "NVDA" in symbols


def test_get_stock_by_symbol() -> None:
    response = client.get("/api/stocks/aapl")

    assert response.status_code == 200

    data = response.json()

    assert data["symbol"] == "AAPL"
    assert data["name"] == "Apple Inc."


def test_stock_not_found() -> None:
    response = client.get("/api/stocks/ZZZZ")

    assert response.status_code == 404

    data = response.json()

    assert data["error"]["code"] == "http_error"
    assert data["error"]["path"] == "/api/stocks/ZZZZ"
