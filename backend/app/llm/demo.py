import json
from typing import TypeVar, cast

from pydantic import BaseModel

from app.core.limits import (
    LLM_MAX_CALLS_PER_ANALYSIS,
    LLM_MAX_INPUT_CHARS,
)
from app.llm.client import LLMCallInfo, LLMClient
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

T = TypeVar(
    "T",
    bound=BaseModel,
)


DEMO_MODEL = "demo-deterministic-v1"

_EVIDENCE_PREFIXES = (
    "price:",
    "financial:",
    "news:",
    "announcement:",
)


_AGENT_SUMMARIES = {
    "fundamental_agent_result": (
        "Demo mode: the fundamental agent processed the "
        "supplied synthetic financial and company evidence."
    ),
    "valuation_agent_result": (
        "Demo mode: the valuation agent processed the "
        "supplied deterministic valuation features."
    ),
    "technical_agent_result": (
        "Demo mode: the technical agent processed the "
        "supplied deterministic market features."
    ),
    "sentiment_agent_result": (
        "Demo mode: the sentiment agent processed the supplied synthetic text evidence."
    ),
    "risk_agent_result": (
        "Demo mode: the risk agent reviewed the supplied "
        "financial, valuation, technical, and event evidence."
    ),
}


class DemoLLMClient(LLMClient):
    """Deterministic local LLM replacement for demos.

    This client never calls an external provider. Its outputs
    are intentionally labeled as synthetic demo results.
    """

    def __init__(self) -> None:
        self.model = DEMO_MODEL
        self.max_calls = LLM_MAX_CALLS_PER_ANALYSIS
        self.max_input_chars = LLM_MAX_INPUT_CHARS
        self._call_count = 0

    def generate_structured(
        self,
        *,
        instructions: str,
        input_text: str,
        schema: type[T],
        schema_name: str,
    ) -> tuple[T, LLMCallInfo]:
        self._check_input_length(
            instructions=instructions,
            input_text=input_text,
        )
        self._reserve_call()

        evidence_ids = _extract_evidence_ids(
            input_text,
        )

        result = _build_demo_result(
            schema=schema,
            schema_name=schema_name,
            evidence_ids=evidence_ids,
        )

        info = LLMCallInfo(
            model=self.model,
            elapsed_ms=0,
            response_id=(f"demo-response-{self._call_count}"),
            request_id=(f"demo-request-{self._call_count}"),
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
        )

        return cast(T, result), info


def _build_demo_result(
    *,
    schema: type[BaseModel],
    schema_name: str,
    evidence_ids: list[str],
) -> BaseModel:
    cited_evidence = evidence_ids[:3]

    if schema is AgentResult:
        summary = _AGENT_SUMMARIES.get(
            schema_name,
            (
                "Demo mode: deterministic synthetic analysis "
                "completed for the supplied evidence."
            ),
        )

        return AgentResult(
            summary=summary,
            positives=[
                (
                    "The supplied fixture contains enough "
                    "structured evidence to demonstrate the "
                    "analysis workflow."
                )
            ],
            negatives=[
                (
                    "Synthetic fixture data cannot establish "
                    "a real-world investment conclusion."
                )
            ],
            evidence_ids=cited_evidence,
            confidence=0.6,
            limitations=[
                (
                    "Demo mode uses deterministic synthetic "
                    "responses and is not investment advice."
                )
            ],
        )

    if schema is BullCase:
        return BullCase(
            overall_thesis=(
                "Demo mode identifies a limited constructive "
                "case from the supplied fixture evidence."
            ),
            claims=[
                BullClaim(
                    claim_id="bull-1",
                    claim=(
                        "The supplied fixture supports a "
                        "limited constructive interpretation."
                    ),
                    rationale=(
                        "This deterministic claim exists to "
                        "demonstrate evidence-grounded debate."
                    ),
                    evidence_ids=cited_evidence,
                    evidence_insufficient=(not bool(cited_evidence)),
                )
            ],
        )

    if schema is BearCase:
        return BearCase(
            rebuttals=[
                BearRebuttal(
                    rebuttal_id="bear-1",
                    bull_claim_id="bull-1",
                    counter_argument=(
                        "The fixture is synthetic and limited, "
                        "so the constructive interpretation "
                        "should not be generalized to actual "
                        "market conditions."
                    ),
                    evidence_ids=cited_evidence,
                    evidence_insufficient=(not bool(cited_evidence)),
                )
            ],
            unresolved_questions=[
                (
                    "Would current real-world disclosures and "
                    "market data materially change the result?"
                )
            ],
        )

    if schema is CrossExamResult:
        return CrossExamResult(
            summary=(
                "Demo cross-examination identifies the main "
                "limitation: the evidence is synthetic."
            ),
            issues=[
                CrossIssue(
                    issue_id="cross-1",
                    category="data_quality",
                    severity="medium",
                    description=(
                        "The workflow is operating on fixed "
                        "demo fixtures rather than live data."
                    ),
                    related_ids=[
                        "bull-1",
                        "bear-1",
                    ],
                    evidence_ids=cited_evidence,
                    evidence_insufficient=(not bool(cited_evidence)),
                )
            ],
            unresolved_questions=[
                (
                    "A real analysis requires current verified "
                    "market and company evidence."
                )
            ],
        )

    if schema is JudgeResult:
        return JudgeResult(
            overall_view=(
                "The deterministic demo completed the full "
                "multi-agent review. The supplied fixture can "
                "demonstrate system behavior, but it should "
                "not be interpreted as a real investment view."
            ),
            key_drivers=[
                (
                    "Structured market and financial fixture "
                    "data are available to the agents."
                )
            ],
            key_risks=[
                ("The underlying evidence and LLM outputs are synthetic demo material.")
            ],
            disputes=[
                (
                    "Bull and Bear interpretations cannot be "
                    "resolved using synthetic evidence alone."
                )
            ],
            point_assessments=[
                JudgePointAssessment(
                    point_id="bull-1",
                    decision="uncertain",
                    reason=(
                        "The claim is suitable for workflow "
                        "demonstration but not for a real-world "
                        "investment conclusion."
                    ),
                    evidence_ids=cited_evidence,
                    evidence_insufficient=(not bool(cited_evidence)),
                )
            ],
            confidence=0.5,
            data_freshness=("Fixed synthetic Day 28 demo fixture."),
            limitations=[
                ("Deterministic demo mode does not call an external LLM provider."),
                (
                    "The output is informational system-demo "
                    "content, not investment advice."
                ),
            ],
        )

    raise ValueError(
        f"Demo LLM does not support schema {schema_name!r} ({schema.__name__})"
    )


def _extract_evidence_ids(
    input_text: str,
) -> list[str]:
    try:
        payload = json.loads(input_text)
    except json.JSONDecodeError:
        return []

    found: set[str] = set()

    def walk(value: object) -> None:
        if isinstance(value, str):
            if value.startswith(
                _EVIDENCE_PREFIXES,
            ):
                found.add(value)
            return

        if isinstance(value, list):
            for item in value:
                walk(item)
            return

        if isinstance(value, dict):
            for item in value.values():
                walk(item)

    walk(payload)

    return sorted(found)
