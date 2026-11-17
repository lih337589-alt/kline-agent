import pytest

from app.agents.base import AgentExecution
from app.agents.registry import AgentRunOutcome
from app.llm.client import LLMCallInfo
from app.schemas.agent import AgentResult
from app.schemas.debate import (
    BearRebuttal,
    BullClaim,
    DebateResult,
)
from app.schemas.review import (
    CrossExamResult,
    CrossIssue,
    JudgePointAssessment,
    JudgeResult,
)
from app.services.report_generator import (
    ReportGenerationError,
    generate_report,
)

PROFESSIONAL_AGENTS = (
    "fundamental",
    "valuation",
    "technical",
    "sentiment",
    "risk",
)


def _llm_call() -> LLMCallInfo:
    return LLMCallInfo(
        model="fake-model",
        elapsed_ms=1,
        response_id="fake-response",
        request_id="fake-request",
        input_tokens=10,
        output_tokens=10,
        total_tokens=20,
    )


def _agent_result(
    agent_name: str,
) -> AgentResult:
    evidence_ids = ["financial:1"]

    if agent_name in {
        "technical",
        "risk",
    }:
        evidence_ids.append("price:105")

    if agent_name == "sentiment":
        evidence_ids = [
            "news:1",
            "news:7",
        ]

    return AgentResult(
        summary=f"{agent_name} summary",
        positives=[f"{agent_name} positive"],
        negatives=[f"{agent_name} negative"],
        evidence_ids=evidence_ids,
        confidence=0.5,
        limitations=[f"{agent_name} limitation"],
    )


def _outcome(
    agent_name: str,
) -> AgentRunOutcome:
    return AgentRunOutcome(
        agent_name=agent_name,
        execution=AgentExecution(
            agent_name=agent_name,
            result=_agent_result(agent_name),
            llm_call=_llm_call(),
        ),
        error_message=None,
        duration_ms=10,
    )


def _outcomes() -> list[AgentRunOutcome]:
    return [_outcome(agent_name) for agent_name in PROFESSIONAL_AGENTS]


def _debate() -> DebateResult:
    return DebateResult(
        bull_claims=[
            BullClaim(
                claim_id="bull-1",
                claim="Profitability is strong.",
                rationale=("Financial evidence supports the claim."),
                evidence_ids=["financial:1"],
                evidence_insufficient=False,
            )
        ],
        bear_rebuttals=[
            BearRebuttal(
                rebuttal_id="bear-1",
                bull_claim_id="bull-1",
                counter_argument=("Only one financial period is available."),
                evidence_ids=["financial:1"],
                evidence_insufficient=False,
            )
        ],
        unresolved_questions=["Is profitability durable?"],
    )


def _cross_exam() -> CrossExamResult:
    return CrossExamResult(
        summary=("The evidence base is limited."),
        issues=[
            CrossIssue(
                issue_id="cross-1",
                category="evidence_gap",
                severity="medium",
                description=("Only one financial period is available."),
                related_ids=[
                    "bull-1",
                    "bear-1",
                ],
                evidence_ids=["financial:1"],
                evidence_insufficient=False,
            )
        ],
        unresolved_questions=["Are more periods available?"],
    )


def _judgment() -> JudgeResult:
    return JudgeResult(
        overall_view=("The evidence is mixed and limited."),
        key_drivers=["Reported profitability."],
        key_risks=["Limited historical data."],
        disputes=["Profitability durability."],
        point_assessments=[
            JudgePointAssessment(
                point_id="bull-1",
                decision="partially_accepted",
                reason=(
                    "The reported figures are supported, but durability is uncertain."
                ),
                evidence_ids=["financial:1"],
                evidence_insufficient=False,
            )
        ],
        confidence=0.4,
        data_freshness=("Data coverage is limited."),
        limitations=["Test data only."],
    )


def test_generate_report_contains_all_sections() -> None:
    report = generate_report(
        symbol="AAPL",
        company_name="Apple Inc.",
        trace_id="trace-test",
        outcomes=_outcomes(),
        debate=_debate(),
        cross_exam=_cross_exam(),
        judgment=_judgment(),
        agent_run_ids=[
            1,
            2,
            3,
            4,
            5,
        ],
    )

    assert report.symbol == "AAPL"
    assert report.company_name == "Apple Inc."
    assert report.trace_id == "trace-test"

    assert report.fundamental.summary == "fundamental summary"

    assert report.valuation.summary == "valuation summary"

    assert report.technical.summary == "technical summary"

    assert report.sentiment.summary == "sentiment summary"

    assert report.risk.summary == "risk summary"

    assert report.debate.bull_claims
    assert report.cross_exam.issues
    assert report.judgment.overall_view == "The evidence is mixed and limited."

    assert report.agent_run_ids == [
        1,
        2,
        3,
        4,
        5,
    ]


def test_executive_summary_uses_judge_view() -> None:
    judgment = _judgment()

    report = generate_report(
        symbol="AAPL",
        company_name="Apple Inc.",
        trace_id="trace-test",
        outcomes=_outcomes(),
        debate=_debate(),
        cross_exam=_cross_exam(),
        judgment=judgment,
        agent_run_ids=[
            1,
            2,
            3,
            4,
            5,
        ],
    )

    assert report.executive_summary == judgment.overall_view


def test_sources_are_deduplicated_and_sorted() -> None:
    report = generate_report(
        symbol="AAPL",
        company_name="Apple Inc.",
        trace_id="trace-test",
        outcomes=_outcomes(),
        debate=_debate(),
        cross_exam=_cross_exam(),
        judgment=_judgment(),
        agent_run_ids=[
            1,
            2,
            3,
            4,
            5,
        ],
    )

    assert report.sources == [
        "financial:1",
        "news:1",
        "news:7",
        "price:105",
    ]

    assert len(report.sources) == len(set(report.sources))


def test_missing_professional_agent_fails() -> None:
    outcomes = [outcome for outcome in _outcomes() if outcome.agent_name != "risk"]

    with pytest.raises(
        ReportGenerationError,
        match="risk",
    ):
        generate_report(
            symbol="AAPL",
            company_name="Apple Inc.",
            trace_id="trace-test",
            outcomes=outcomes,
            debate=_debate(),
            cross_exam=_cross_exam(),
            judgment=_judgment(),
            agent_run_ids=[
                1,
                2,
                3,
                4,
            ],
        )
