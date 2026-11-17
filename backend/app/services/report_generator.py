from app.agents.registry import AgentRunOutcome
from app.schemas.agent import AgentResult
from app.schemas.debate import DebateResult
from app.schemas.report import ReportPayload
from app.schemas.review import (
    CrossExamResult,
    JudgeResult,
)


class ReportGenerationError(ValueError):
    pass


_REQUIRED_AGENTS = (
    "fundamental",
    "valuation",
    "technical",
    "sentiment",
    "risk",
)


def generate_report(
    *,
    symbol: str,
    company_name: str,
    trace_id: str,
    outcomes: list[AgentRunOutcome],
    debate: DebateResult,
    cross_exam: CrossExamResult,
    judgment: JudgeResult,
    agent_run_ids: list[int],
) -> ReportPayload:
    agent_results = _collect_agent_results(outcomes)

    sources = _collect_sources(agent_results)

    return ReportPayload(
        symbol=symbol,
        company_name=company_name,
        trace_id=trace_id,
        executive_summary=(judgment.overall_view),
        fundamental=agent_results["fundamental"],
        valuation=agent_results["valuation"],
        technical=agent_results["technical"],
        sentiment=agent_results["sentiment"],
        risk=agent_results["risk"],
        debate=debate,
        cross_exam=cross_exam,
        judgment=judgment,
        sources=sources,
        agent_run_ids=agent_run_ids,
    )


def _collect_agent_results(
    outcomes: list[AgentRunOutcome],
) -> dict[str, AgentResult]:
    results: dict[str, AgentResult] = {}

    for outcome in outcomes:
        if outcome.execution is None:
            continue

        results[outcome.agent_name] = outcome.execution.result

    missing_agents = [
        agent_name for agent_name in _REQUIRED_AGENTS if agent_name not in results
    ]

    if missing_agents:
        raise ReportGenerationError(
            "Cannot generate report because "
            "professional agent results are "
            "missing: " + ", ".join(missing_agents)
        )

    return results


def _collect_sources(
    agent_results: dict[
        str,
        AgentResult,
    ],
) -> list[str]:
    evidence_ids: set[str] = set()

    for result in agent_results.values():
        evidence_ids.update(result.evidence_ids)

    return sorted(evidence_ids)
