from app.agents.base import AgentExecution
from app.agents.bear import BearAgent, BearExecution
from app.agents.bull import BullAgent, BullExecution
from app.agents.cross_examiner import (
    CrossExamExecution,
    CrossExaminerAgent,
)
from app.agents.fundamental import FundamentalAgent
from app.agents.judge import (
    JudgeAgent,
    JudgeExecution,
)
from app.agents.risk import RiskAgent
from app.agents.sentiment import SentimentAgent
from app.agents.technical import TechnicalAgent
from app.agents.valuation import ValuationAgent
from app.llm.client import (
    LLMCallInfo,
    LLMProviderError,
)
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
from app.workflows.analysis import AnalysisWorkflow

PROFESSIONAL_AGENT_ORDER = [
    "fundamental",
    "valuation",
    "technical",
    "sentiment",
    "risk",
]

FULL_WORKFLOW_ORDER = [
    *PROFESSIONAL_AGENT_ORDER,
    "bull",
    "bear",
    "cross_examiner",
    "judge",
]


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


def _execution(
    agent_name: str,
) -> AgentExecution:
    return AgentExecution(
        agent_name=agent_name,
        result=AgentResult(
            summary=f"{agent_name} result",
            positives=[],
            negatives=[],
            evidence_ids=[],
            confidence=0.5,
            limitations=[],
        ),
        llm_call=_llm_call(),
    )


def _bull_execution() -> BullExecution:
    return BullExecution(
        result=BullCase(
            overall_thesis="Limited bullish thesis.",
            claims=[
                BullClaim(
                    claim_id="bull-1",
                    claim="Bull claim.",
                    rationale="Workflow test.",
                    evidence_ids=[],
                    evidence_insufficient=True,
                )
            ],
        ),
        llm_call=_llm_call(),
    )


def _bear_execution() -> BearExecution:
    return BearExecution(
        result=BearCase(
            rebuttals=[
                BearRebuttal(
                    rebuttal_id="bear-1",
                    bull_claim_id="bull-1",
                    counter_argument="Bear rebuttal.",
                    evidence_ids=[],
                    evidence_insufficient=True,
                )
            ],
            unresolved_questions=[],
        ),
        llm_call=_llm_call(),
    )


def _cross_execution() -> CrossExamExecution:
    return CrossExamExecution(
        result=CrossExamResult(
            summary="Evidence remains limited.",
            issues=[
                CrossIssue(
                    issue_id="cross-1",
                    category="evidence_gap",
                    severity="medium",
                    description="Evidence is limited.",
                    related_ids=["bull-1"],
                    evidence_ids=[],
                    evidence_insufficient=True,
                )
            ],
            unresolved_questions=[],
        ),
        llm_call=_llm_call(),
    )


def _judge_execution() -> JudgeExecution:
    return JudgeExecution(
        result=JudgeResult(
            overall_view="Evidence is mixed.",
            key_drivers=["Limited positive evidence."],
            key_risks=["Evidence limitations."],
            disputes=["Bull versus Bear dispute."],
            point_assessments=[
                JudgePointAssessment(
                    point_id="bull-1",
                    decision="uncertain",
                    reason="Insufficient evidence.",
                    evidence_ids=[],
                    evidence_insufficient=True,
                )
            ],
            confidence=0.4,
            data_freshness=("Data quality is limited."),
            limitations=["Test data only."],
        ),
        llm_call=_llm_call(),
    )


def _success_run(
    agent_name: str,
    calls: list[str],
):
    def run(
        _self,
        *_args,
        **_kwargs,
    ):
        calls.append(agent_name)
        return _execution(agent_name)

    return run


def _patch_professional_agents(
    monkeypatch,
    calls: list[str],
) -> None:
    agents = [
        (FundamentalAgent, "fundamental"),
        (ValuationAgent, "valuation"),
        (TechnicalAgent, "technical"),
        (SentimentAgent, "sentiment"),
        (RiskAgent, "risk"),
    ]

    for agent_class, agent_name in agents:
        monkeypatch.setattr(
            agent_class,
            "run",
            _success_run(
                agent_name,
                calls,
            ),
        )


def _patch_review_agents(
    monkeypatch,
    calls: list[str],
) -> None:
    def bull_run(
        _self,
        *_args,
        **_kwargs,
    ):
        calls.append("bull")
        return _bull_execution()

    def bear_run(
        _self,
        *_args,
        **_kwargs,
    ):
        calls.append("bear")
        return _bear_execution()

    def cross_run(
        _self,
        *_args,
        **_kwargs,
    ):
        calls.append("cross_examiner")
        return _cross_execution()

    def judge_run(
        _self,
        *_args,
        **_kwargs,
    ):
        calls.append("judge")
        return _judge_execution()

    monkeypatch.setattr(
        BullAgent,
        "run",
        bull_run,
    )

    monkeypatch.setattr(
        BearAgent,
        "run",
        bear_run,
    )

    monkeypatch.setattr(
        CrossExaminerAgent,
        "run",
        cross_run,
    )

    monkeypatch.setattr(
        JudgeAgent,
        "run",
        judge_run,
    )


def test_workflow_runs_full_review_in_order(
    monkeypatch,
) -> None:
    calls: list[str] = []

    _patch_professional_agents(
        monkeypatch,
        calls,
    )

    _patch_review_agents(
        monkeypatch,
        calls,
    )

    workflow = AnalysisWorkflow(llm_client=object())

    result = workflow.run(
        trace_id="trace-test",
        context=object(),
        technical_features=object(),
        valuation_features=object(),
    )

    assert calls == FULL_WORKFLOW_ORDER

    assert result.success_count == 5
    assert result.error_count == 0

    assert result.debate_succeeded
    assert result.cross_succeeded
    assert result.judge_succeeded
    assert result.analysis_succeeded

    assert result.debate is not None
    assert result.cross_exam is not None
    assert result.judgment is not None


def test_professional_failure_isolated(
    monkeypatch,
) -> None:
    calls: list[str] = []

    _patch_professional_agents(
        monkeypatch,
        calls,
    )

    _patch_review_agents(
        monkeypatch,
        calls,
    )

    def failed_sentiment(
        _self,
        *_args,
        **_kwargs,
    ):
        calls.append("sentiment")

        raise LLMProviderError("simulated provider failure")

    monkeypatch.setattr(
        SentimentAgent,
        "run",
        failed_sentiment,
    )

    workflow = AnalysisWorkflow(llm_client=object())

    result = workflow.run(
        context=object(),
        technical_features=object(),
        valuation_features=object(),
    )

    assert calls == FULL_WORKFLOW_ORDER

    assert result.success_count == 4
    assert result.error_count == 1

    assert result.debate is not None
    assert result.cross_exam is not None
    assert result.judgment is not None

    assert result.analysis_succeeded is False


def test_bull_failure_stops_downstream_llm_calls(
    monkeypatch,
) -> None:
    calls: list[str] = []

    _patch_professional_agents(
        monkeypatch,
        calls,
    )

    def failed_bull(
        _self,
        *_args,
        **_kwargs,
    ):
        calls.append("bull")

        raise LLMProviderError("simulated bull failure")

    monkeypatch.setattr(
        BullAgent,
        "run",
        failed_bull,
    )

    workflow = AnalysisWorkflow(llm_client=object())

    result = workflow.run(
        context=object(),
        technical_features=object(),
        valuation_features=object(),
    )

    assert calls == [
        *PROFESSIONAL_AGENT_ORDER,
        "bull",
    ]

    assert result.debate is None
    assert result.cross_exam is None
    assert result.judgment is None

    assert result.debate_error is not None
    assert result.cross_error is not None
    assert result.judge_error is not None


def test_cross_failure_stops_judge_llm_call(
    monkeypatch,
) -> None:
    calls: list[str] = []

    _patch_professional_agents(
        monkeypatch,
        calls,
    )

    def bull_run(
        _self,
        *_args,
        **_kwargs,
    ):
        calls.append("bull")
        return _bull_execution()

    def bear_run(
        _self,
        *_args,
        **_kwargs,
    ):
        calls.append("bear")
        return _bear_execution()

    def failed_cross(
        _self,
        *_args,
        **_kwargs,
    ):
        calls.append("cross_examiner")

        raise LLMProviderError("simulated cross failure")

    monkeypatch.setattr(
        BullAgent,
        "run",
        bull_run,
    )

    monkeypatch.setattr(
        BearAgent,
        "run",
        bear_run,
    )

    monkeypatch.setattr(
        CrossExaminerAgent,
        "run",
        failed_cross,
    )

    workflow = AnalysisWorkflow(llm_client=object())

    result = workflow.run(
        context=object(),
        technical_features=object(),
        valuation_features=object(),
    )

    assert calls == [
        *PROFESSIONAL_AGENT_ORDER,
        "bull",
        "bear",
        "cross_examiner",
    ]

    assert result.debate is not None
    assert result.cross_exam is None
    assert result.judgment is None

    assert result.cross_error is not None
    assert result.judge_error is not None

    assert "simulated cross failure" in result.cross_error
