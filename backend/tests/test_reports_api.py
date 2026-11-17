from datetime import (
    UTC,
    datetime,
)

from fastapi.testclient import TestClient

from app.api.routes import reports as reports_route
from app.main import app

client = TestClient(app)


def _report_response() -> dict[str, object]:
    return {
        "id": 123,
        "stock_id": 1,
        "symbol": "AAPL",
        "trace_id": "trace-api-test",
        "title": ("AAPL Multi-Agent Research Report"),
        "status": "completed",
        "source": "test",
        "report": {
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "trace_id": "trace-api-test",
            "executive_summary": ("Evidence is mixed."),
            "fundamental": {
                "summary": ("Fundamental summary."),
                "positives": [],
                "negatives": [],
                "evidence_ids": ["financial:1"],
                "confidence": 0.5,
                "limitations": [],
            },
            "valuation": {
                "summary": ("Valuation summary."),
                "positives": [],
                "negatives": [],
                "evidence_ids": ["financial:1"],
                "confidence": 0.5,
                "limitations": [],
            },
            "technical": {
                "summary": ("Technical summary."),
                "positives": [],
                "negatives": [],
                "evidence_ids": ["price:105"],
                "confidence": 0.5,
                "limitations": [],
            },
            "sentiment": {
                "summary": ("Sentiment summary."),
                "positives": [],
                "negatives": [],
                "evidence_ids": ["news:1"],
                "confidence": 0.3,
                "limitations": [],
            },
            "risk": {
                "summary": ("Risk summary."),
                "positives": [],
                "negatives": [],
                "evidence_ids": [
                    "financial:1",
                    "price:105",
                ],
                "confidence": 0.4,
                "limitations": [],
            },
            "debate": {
                "bull_claims": [
                    {
                        "claim_id": "bull-1",
                        "claim": ("Bull claim."),
                        "rationale": ("Test rationale."),
                        "evidence_ids": ["financial:1"],
                        "evidence_insufficient": (False),
                    }
                ],
                "bear_rebuttals": [
                    {
                        "rebuttal_id": ("bear-1"),
                        "bull_claim_id": ("bull-1"),
                        "counter_argument": ("Bear rebuttal."),
                        "evidence_ids": ["financial:1"],
                        "evidence_insufficient": (False),
                    }
                ],
                "unresolved_questions": [],
            },
            "cross_exam": {
                "summary": ("Evidence is limited."),
                "issues": [
                    {
                        "issue_id": ("cross-1"),
                        "category": ("evidence_gap"),
                        "severity": "medium",
                        "description": ("More evidence is needed."),
                        "related_ids": ["bull-1"],
                        "evidence_ids": ["financial:1"],
                        "evidence_insufficient": (False),
                    }
                ],
                "unresolved_questions": [],
            },
            "judgment": {
                "overall_view": ("Evidence is mixed."),
                "key_drivers": ["Test driver."],
                "key_risks": ["Test risk."],
                "disputes": ["Test dispute."],
                "point_assessments": [
                    {
                        "point_id": ("bull-1"),
                        "decision": ("uncertain"),
                        "reason": ("Evidence is limited."),
                        "evidence_ids": ["financial:1"],
                        "evidence_insufficient": (False),
                    }
                ],
                "confidence": 0.4,
                "data_freshness": ("Test data."),
                "limitations": ["Test limitation."],
            },
            "sources": [
                "financial:1",
                "news:1",
                "price:105",
            ],
            "agent_run_ids": [
                1,
                2,
                3,
                4,
                5,
            ],
        },
        "created_at": datetime(
            2026,
            9,
            17,
            12,
            0,
            tzinfo=UTC,
        ).isoformat(),
    }


def test_get_report_success(
    monkeypatch,
) -> None:
    def fake_read_report(
        _db,
        report_id: int,
    ):
        assert report_id == 123
        return _report_response()

    monkeypatch.setattr(
        reports_route,
        "read_report",
        fake_read_report,
    )

    response = client.get("/api/reports/123")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 123
    assert data["symbol"] == "AAPL"
    assert data["status"] == "completed"

    assert data["report"]["executive_summary"] == "Evidence is mixed."

    assert len(data["report"]["agent_run_ids"]) == 5


def test_get_report_not_found(
    monkeypatch,
) -> None:
    def fake_read_report(
        _db,
        _report_id: int,
    ):
        return None

    monkeypatch.setattr(
        reports_route,
        "read_report",
        fake_read_report,
    )

    response = client.get("/api/reports/999999")

    assert response.status_code == 404

    data = response.json()

    assert data["error"]["code"] == "http_error"
    assert data["error"]["path"] == "/api/reports/999999"
