import json
from dataclasses import dataclass

from app.agents.registry import AgentRunOutcome
from app.llm.client import LLMCallInfo, LLMClient
from app.schemas.debate import DebateResult
from app.schemas.review import CrossExamResult


@dataclass(frozen=True)
class CrossExamExecution:
    result: CrossExamResult
    llm_call: LLMCallInfo


class CrossExaminerAgent:
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
    ) -> CrossExamExecution:
        allowed_evidence_ids = self._collect_evidence_ids(outcomes)

        valid_related_ids = self._collect_related_ids(
            outcomes,
            debate,
        )

        input_text = json.dumps(
            {
                "professional_agent_results": (self._serialize_outcomes(outcomes)),
                "debate": debate.model_dump(mode="json"),
                "allowed_evidence_ids": sorted(allowed_evidence_ids),
                "allowed_related_ids": sorted(valid_related_ids),
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )

        instructions = """
You are the Cross Examiner in an evidence-grounded
financial research workflow.

Your role is to audit evidence quality and reasoning
quality.

You are NOT the Bull Agent.
You are NOT the Bear Agent.
You are NOT the final Judge.

Do not decide which side wins.

Inspect the professional-agent results and Bull/Bear
debate for the following problems:

1. Conflicting data dates.

2. Stale evidence.

3. Missing evidence.

4. Logical jumps between evidence and conclusions.

5. Different definitions, periods, or measurement
   windows being treated as equivalent.

6. Contradictions between professional agents.

7. Contradictions between Bull and Bear.

8. Synthetic, mock, sample, placeholder, or otherwise
   low-quality evidence.

9. Claims that are stronger than the supplied evidence
   supports.

Return exactly one JSON object with this structure:

{
  "summary": "...",
  "issues": [
    {
      "issue_id": "cross-1",
      "category": "data_quality",
      "severity": "high",
      "description": "...",
      "related_ids": ["bull-1"],
      "evidence_ids": ["financial:1"],
      "evidence_insufficient": false
    }
  ],
  "unresolved_questions": [
    "..."
  ]
}

Allowed category values:

date_conflict
evidence_gap
logic_gap
metric_mismatch
data_quality
other

Allowed severity values:

low
medium
high

RULES:

1. issue_id values must be unique.

2. Use issue IDs exactly in this style:
   cross-1
   cross-2
   cross-3

3. related_ids must be copied exactly from
   allowed_related_ids.

4. evidence_ids must be copied exactly from
   allowed_evidence_ids.

5. Never invent an evidence ID.

6. If evidence_ids is empty:
   evidence_insufficient MUST be true.

7. If evidence_ids is non-empty:
   evidence_insufficient MUST be false.

8. Do not introduce outside facts.

9. Do not provide investment advice.

10. Do not predict guaranteed future price movement.

11. Focus on evidence quality and reasoning quality,
    not whether Bull or Bear should win.

12. Keep each issue description concise.
    Prefer approximately 1 to 3 sentences.

13. Prefer the smallest set of distinct issues needed
    to explain the material reasoning problems.

14. Avoid repeating the same evidence-quality problem
    in multiple issues.

15. Keep unresolved_questions concise.

16. Do not create an issue merely to increase the
    number of issues.

17. Prioritize material problems over minor wording
    differences.

18. Output only data matching the required schema.
""".strip()

        result, llm_call = self._llm.generate_structured(
            instructions=instructions,
            input_text=input_text,
            schema=CrossExamResult,
            schema_name="cross_exam_result",
        )

        self._validate_evidence_ids(
            result,
            allowed_evidence_ids,
        )

        self._validate_related_ids(
            result,
            valid_related_ids,
        )

        return CrossExamExecution(
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
    def _collect_related_ids(
        outcomes: list[AgentRunOutcome],
        debate: DebateResult,
    ) -> set[str]:
        related_ids = {outcome.agent_name for outcome in outcomes}

        related_ids.update(claim.claim_id for claim in debate.bull_claims)

        related_ids.update(rebuttal.rebuttal_id for rebuttal in debate.bear_rebuttals)

        return related_ids

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
        result: CrossExamResult,
        allowed_evidence_ids: set[str],
    ) -> None:
        for issue in result.issues:
            invalid_ids = set(issue.evidence_ids) - allowed_evidence_ids

            if invalid_ids:
                raise ValueError(
                    "Cross Examiner returned unknown "
                    "evidence IDs: "
                    f"{sorted(invalid_ids)}"
                )

    @staticmethod
    def _validate_related_ids(
        result: CrossExamResult,
        valid_related_ids: set[str],
    ) -> None:
        for issue in result.issues:
            invalid_ids = set(issue.related_ids) - valid_related_ids

            if invalid_ids:
                raise ValueError(
                    "Cross Examiner returned unknown "
                    "related IDs: "
                    f"{sorted(invalid_ids)}"
                )
