import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
)
def test_cors_allows_frontend_post_preflight(
    origin: str,
) -> None:
    response = client.options(
        "/api/analyses",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200

    assert response.headers["access-control-allow-origin"] == origin

    assert "POST" in response.headers["access-control-allow-methods"]


def test_cors_does_not_allow_unknown_origin() -> None:
    response = client.options(
        "/api/analyses",
        headers={
            "Origin": "https://example.invalid",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.headers.get("access-control-allow-origin") is None
