from datetime import (
    date,
    datetime,
    timedelta,
    timezone,
)
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy import select

from app.database.session import SessionLocal
from app.llm.client import (
    LLMCallInfo,
    LLMClient,
)
from app.main import app
from app.models.agent_run import AgentRun
from app.models.financial import Financial
from app.models.price import Price
from app.models.stock import Stock
from app.schemas.agent import AgentResult
from app.schemas.debate import (
    BearCase,
    BearRebuttal,
    BullCase,
    BullClaim,
)
from app.schemas.review import (
    CrossExamResult,
    CrossIssue,
    JudgePointAssessment,
    JudgeResult,
)

client = TestClient(app)


PROFESSIONAL_AGENTS = {
    "fundamental",
    "valuation",
    "technical",
    "sentiment",
    "risk",
}


def _fake_llm_init(
    self: LLMClient,
    *args: object,
    **kwargs: object,
) -> None:
    del args
    del kwargs

    self.model = "fake-smoke-model"
    self.max_calls = 100
    self.max_input_chars = 1_000_000
    self._call_count = 0


def _fake_generate_structured(
    self: LLMClient,
    *,
    instructions: str,
    input_text: str,
    schema: type[BaseModel],
    schema_name: str,
) -> tuple[
    BaseModel,
    LLMCallInfo,
]:
    del instructions
    del input_text

    self._call_count += 1

    if schema is AgentResult:
        result: BaseModel = AgentResult(
            summary=(f"{schema_name} smoke-test summary."),
            positives=["Fixture data is available."],
            negatives=[],
            evidence_ids=[],
            confidence=0.8,
            limitations=["Fixture data only."],
        )

    elif schema is BullCase:
        result = BullCase(
            overall_thesis=("The fixture provides a limited bullish case."),
            claims=[
                BullClaim(
                    claim_id="bull-1",
                    claim=("The fixture contains positive evidence."),
                    rationale=("This is a deterministic smoke-test response."),
                    evidence_ids=[],
                    evidence_insufficient=True,
                )
            ],
        )

    elif schema is BearCase:
        result = BearCase(
            rebuttals=[
                BearRebuttal(
                    rebuttal_id="bear-1",
                    bull_claim_id="bull-1",
                    counter_argument=(
                        "The fixture is too limited for a strong conclusion."
                    ),
                    evidence_ids=[],
                    evidence_insufficient=True,
                )
            ],
            unresolved_questions=["Would additional evidence change the assessment?"],
        )

    elif schema is CrossExamResult:
        result = CrossExamResult(
            summary=("The fixture evidence remains limited."),
            issues=[
                CrossIssue(
                    issue_id="cross-1",
                    category="evidence_gap",
                    severity="medium",
                    description=("The smoke-test fixture contains limited evidence."),
                    related_ids=[
                        "bull-1",
                        "bear-1",
                    ],
                    evidence_ids=[],
                    evidence_insufficient=True,
                )
            ],
            unresolved_questions=[
                "More evidence would be needed for a stronger conclusion."
            ],
        )

    elif schema is JudgeResult:
        result = JudgeResult(
            overall_view=(
                "The smoke-test analysis "
                "completed successfully with "
                "limited fixture evidence."
            ),
            key_drivers=[
                "The deterministic fixture contains market and financial data."
            ],
            key_risks=["The fixture is intentionally limited."],
            disputes=["The strength of the available evidence remains uncertain."],
            point_assessments=[
                JudgePointAssessment(
                    point_id="bull-1",
                    decision="uncertain",
                    reason=(
                        "The fixture is sufficient "
                        "for a smoke test but not "
                        "for a strong conclusion."
                    ),
                    evidence_ids=[],
                    evidence_insufficient=True,
                )
            ],
            confidence=0.5,
            data_freshness=("Synthetic fixture data."),
            limitations=["Smoke-test fixture only."],
        )

    else:
        raise AssertionError(
            f"Unexpected structured LLM schema: {schema_name} ({schema.__name__})"
        )

    return (
        result,
        LLMCallInfo(
            model="fake-smoke-model",
            elapsed_ms=1,
            response_id="fake-response",
            request_id="fake-request",
            input_tokens=10,
            output_tokens=10,
            total_tokens=20,
        ),
    )


def _create_fixture_stock() -> tuple[
    int,
    str,
]:
    symbol = "E" + uuid4().hex[:8].upper()

    with SessionLocal() as db:
        stock = Stock(
            symbol=symbol,
            name="E2E Smoke Test Stock",
            exchange="TEST",
            industry="Testing",
        )

        db.add(stock)
        db.commit()
        db.refresh(stock)

        stock_id = stock.id

        start = datetime(
            2026,
            1,
            1,
            tzinfo=timezone.utc,
        )

        for index in range(21):
            db.add(
                Price(
                    stock_id=stock_id,
                    timestamp=(start + timedelta(days=index)),
                    close=Decimal(str(100 + index)),
                    volume=(1_000 + index),
                    source="e2e-smoke",
                )
            )

        db.add(
            Financial(
                stock_id=stock_id,
                period_end=date(
                    2025,
                    12,
                    31,
                ),
                period_type="annual",
                revenue=Decimal(1000),
                net_income=Decimal(100),
                eps=Decimal(5),
                roe=Decimal("0.20"),
                operating_cash_flow=(Decimal(150)),
                source="e2e-smoke",
            )
        )

        db.commit()

    return (
        stock_id,
        symbol,
    )


def _delete_fixture_stock(
    stock_id: int,
) -> None:
    with SessionLocal() as db:
        stock = db.get(
            Stock,
            stock_id,
        )

        if stock is not None:
            db.delete(stock)
            db.commit()


def test_seed_to_analysis_to_report_smoke(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        LLMClient,
        "__init__",
        _fake_llm_init,
    )

    monkeypatch.setattr(
        LLMClient,
        "generate_structured",
        _fake_generate_structured,
    )

    stock_id, symbol = _create_fixture_stock()

    try:
        analysis_response = client.post(
            "/api/analyses",
            json={
                "symbol": (symbol.lower()),
                "use_cache": False,
            },
        )

        assert analysis_response.status_code in {
            200,
            201,
        }, analysis_response.text

        analysis_data = analysis_response.json()

        assert analysis_data["symbol"] == symbol

        assert analysis_data["report_id"] > 0

        assert analysis_data["trace_id"]

        assert analysis_data["status"]

        report_id = analysis_data["report_id"]

        trace_id = analysis_data["trace_id"]

        report_response = client.get(f"/api/reports/{report_id}")

        assert report_response.status_code == 200, report_response.text

        report_data = report_response.json()

        assert report_data["id"] == report_id

        assert report_data["stock_id"] == stock_id

        assert report_data["symbol"] == symbol

        assert report_data["trace_id"] == trace_id

        assert report_data["status"] == "completed"

        payload = report_data["report"]

        assert payload["symbol"] == symbol

        assert payload["company_name"] == ("E2E Smoke Test Stock")

        assert payload["trace_id"] == trace_id

        assert payload["executive_summary"] == (
            "The smoke-test "
            "analysis completed "
            "successfully with "
            "limited fixture "
            "evidence."
        )

        for agent_name in PROFESSIONAL_AGENTS:
            result = payload[agent_name]

            assert result["summary"]

            assert 0.0 <= result["confidence"] <= 1.0

            assert isinstance(
                result["evidence_ids"],
                list,
            )

            assert isinstance(
                result["limitations"],
                list,
            )

        assert payload["debate"]["bull_claims"]

        assert payload["debate"]["bear_rebuttals"]

        assert payload["cross_exam"]["issues"]

        assert payload["judgment"]["overall_view"]

        assert len(payload["agent_run_ids"]) == 5

        with SessionLocal() as db:
            agent_runs = list(
                db.scalars(select(AgentRun).where(AgentRun.trace_id == trace_id)).all()
            )

        assert len(agent_runs) == 5

        assert {run.agent_type for run in agent_runs} == PROFESSIONAL_AGENTS

        assert all(run.status == "success" for run in agent_runs)

        assert all(run.model_name == "fake-smoke-model" for run in agent_runs)

    finally:
        _delete_fixture_stock(stock_id)
