import json
from dataclasses import dataclass

from app.agents.registry import AgentRunOutcome
from app.llm.client import LLMCallInfo, LLMClient
from app.schemas.debate import DebateResult
from app.schemas.review import (
    CrossExamResult,
    JudgeResult,
)


@dataclass(frozen=True)
class JudgeExecution:
    result: JudgeResult
    llm_call: LLMCallInfo


class JudgeAgent:
    def __init__(
        self,
        llm_client: LLMClient,
    ) -> None:
        self._llm = llm_client

    def run(
        self,
        *,
        outcomes: list[AgentRunOutcome],
        debate: DebateResult,
        cross_exam: CrossExamResult,
    ) -> JudgeExecution:
        allowed_evidence_ids = self._collect_evidence_ids(outcomes)

        valid_point_ids = self._collect_point_ids(
            outcomes,
            debate,
            cross_exam,
        )

        input_text = json.dumps(
            {
                "professional_agent_results": (self._serialize_outcomes(outcomes)),
                "debate": debate.model_dump(mode="json"),
                "cross_exam": cross_exam.model_dump(mode="json"),
                "allowed_evidence_ids": sorted(allowed_evidence_ids),
                "allowed_point_ids": sorted(valid_point_ids),
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )

        instructions = """
You are the Judge in an evidence-grounded financial
research workflow.

You may use ONLY the supplied:

1. Professional-agent results.
2. Bull/Bear debate.
3. Cross Examiner result.

Do not introduce outside facts.

Your job is to synthesize the supplied analysis and
explain which important claims should be accepted,
rejected, partially accepted, or left uncertain.

Return exactly one JSON object with this structure:

{
  "overall_view": "...",
  "key_drivers": [
    "..."
  ],
  "key_risks": [
    "..."
  ],
  "disputes": [
    "..."
  ],
  "point_assessments": [
    {
      "point_id": "bull-1",
      "decision": "partially_accepted",
      "reason": "...",
      "evidence_ids": ["financial:1"],
      "evidence_insufficient": false
    }
  ],
  "confidence": 0.5,
  "data_freshness": "...",
  "limitations": [
    "..."
  ]
}

Allowed decision values:

accepted
rejected
partially_accepted
uncertain

RULES:

1. Explain WHY important arguments are accepted,
   rejected, partially accepted, or uncertain.

2. point_id must be copied exactly from
   allowed_point_ids.

3. evidence_ids must be copied exactly from
   allowed_evidence_ids.

4. Never invent an evidence ID.

5. If evidence_ids is empty:
   evidence_insufficient MUST be true.

6. If evidence_ids is non-empty:
   evidence_insufficient MUST be false.

7. confidence measures confidence in the QUALITY
   and RELIABILITY of the analysis.

8. confidence is NOT the probability that the stock
   will rise or fall.

9. Do not describe confidence as a directional
   probability or expected return.

10. data_freshness must explain whether evidence is
    current, stale, mixed-date, synthetic, incomplete,
    or otherwise limited.

11. Preserve unresolved disputes when evidence does
    not support a definitive conclusion.

12. Never guarantee future price appreciation.

13. Never guarantee future price decline.

14. Do not provide personalized investment advice.

15. Keep each point-assessment reason concise.
    Use 1 to 2 sentences.

16. Produce at most 12 point_assessments.
    You are NOT required to assess every
    allowed_point_id.

17. Select only the most decision-relevant point_ids.
    Prioritize major claims, rebuttals, cross-exam
    issues, evidence-quality problems, and risks.

18. Use at most 3 evidence_ids in each
    point_assessment.

19. Do not assess every minor wording difference.

20. Avoid repeating the same limitation in
    overall_view, disputes, point_assessments, and
    limitations.

21. Keep overall_view concise and evidence grounded.
    Prefer 3 to 5 sentences.

22. Return at most 4 key_drivers, 4 key_risks,
    4 disputes, and 4 limitations.

23. Do not treat a high confidence value as a bullish
    signal.

24. Do not treat a low confidence value as a bearish
    signal.

25. Output only data matching the required schema.
""".strip()

        result, llm_call = self._llm.generate_structured(
            instructions=instructions,
            input_text=input_text,
            schema=JudgeResult,
            schema_name="judge_result",
        )

        self._validate_evidence_ids(
            result,
            allowed_evidence_ids,
        )

        self._validate_point_ids(
            result,
            valid_point_ids,
        )

        return JudgeExecution(
            result=result,
            llm_call=llm_call,
        )

    @staticmethod
    def _collect_evidence_ids(
        outcomes: list[AgentRunOutcome],
    ) -> set[str]:
        evidence_ids: set[str] = set()

        for outcome in outcomes:
            if outcome.execution is None:
                continue

            evidence_ids.update(outcome.execution.result.evidence_ids)

        return evidence_ids

    @staticmethod
    def _collect_point_ids(
        outcomes: list[AgentRunOutcome],
        debate: DebateResult,
        cross_exam: CrossExamResult,
    ) -> set[str]:
        point_ids = {outcome.agent_name for outcome in outcomes}

        point_ids.update(claim.claim_id for claim in debate.bull_claims)

        point_ids.update(rebuttal.rebuttal_id for rebuttal in debate.bear_rebuttals)

        point_ids.update(issue.issue_id for issue in cross_exam.issues)

        return point_ids

    @staticmethod
    def _serialize_outcomes(
        outcomes: list[AgentRunOutcome],
    ) -> list[dict[str, object]]:
        serialized: list[dict[str, object]] = []

        for outcome in outcomes:
            if outcome.execution is None:
                serialized.append(
                    {
                        "agent": outcome.agent_name,
                        "status": "error",
                        "error": outcome.error_message,
                    }
                )
                continue

            serialized.append(
                {
                    "agent": outcome.agent_name,
                    "status": "success",
                    "result": (outcome.execution.result.model_dump(mode="json")),
                }
            )

        return serialized

    @staticmethod
    def _validate_evidence_ids(
        result: JudgeResult,
        allowed_evidence_ids: set[str],
    ) -> None:
        for assessment in result.point_assessments:
            invalid_ids = set(assessment.evidence_ids) - allowed_evidence_ids

            if invalid_ids:
                raise ValueError(
                    f"Judge returned unknown evidence IDs: {sorted(invalid_ids)}"
                )

    @staticmethod
    def _validate_point_ids(
        result: JudgeResult,
        valid_point_ids: set[str],
    ) -> None:
        for assessment in result.point_assessments:
            if assessment.point_id not in valid_point_ids:
                raise ValueError(
                    f"Judge returned unknown point_id: {assessment.point_id}"
                )
