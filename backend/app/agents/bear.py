import json
from dataclasses import dataclass

from app.agents.registry import AgentRunOutcome
from app.llm.client import LLMCallInfo, LLMClient
from app.schemas.debate import BearCase, BullCase


@dataclass(frozen=True)
class BearExecution:
    result: BearCase
    llm_call: LLMCallInfo


class BearAgent:
    def __init__(
        self,
        llm_client: LLMClient,
    ) -> None:
        self._llm = llm_client

    def run(
        self,
        *,
        bull_case: BullCase,
        outcomes: list[AgentRunOutcome],
    ) -> BearExecution:
        allowed_evidence_ids = self._collect_evidence_ids(outcomes)

        input_text = json.dumps(
            {
                "bull_case": bull_case.model_dump(mode="json"),
                "professional_agent_results": (self._serialize_outcomes(outcomes)),
                "allowed_evidence_ids": sorted(allowed_evidence_ids),
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )

        instructions = """
You are the Bear Agent in an evidence-grounded
financial research debate.

Your job is NOT to write an independent bearish report.

Your job is to directly rebut every Bull claim using
only the supplied professional-agent results and
allowed evidence.

Return exactly one JSON object with these top-level
keys:

{
  "rebuttals": [
    {
      "rebuttal_id": "bear-1",
      "bull_claim_id": "bull-1",
      "counter_argument": "...",
      "evidence_ids": ["financial:1"],
      "evidence_insufficient": false
    }
  ],
  "unresolved_questions": [
    "..."
  ]
}

Do NOT add any other top-level fields.

REBUTTAL RULES:

1. Produce exactly one rebuttal for every Bull claim.

2. Copy each bull_claim_id exactly from the Bull case.

3. Every Bull claim must be rebutted exactly once.

4. Do not invent a bull_claim_id.

5. rebuttal_id values must be unique.

6. Use rebuttal IDs in this style:
   bear-1
   bear-2
   bear-3
   bear-4
   bear-5

7. Every evidence ID must be copied exactly from
   allowed_evidence_ids.

8. Never invent an evidence ID.

9. If evidence_ids contains one or more IDs:
   evidence_insufficient MUST be false.

10. If evidence_ids is empty:
    evidence_insufficient MUST be true.

11. Never set evidence_insufficient=true when
    evidence_ids is non-empty.

12. Never set evidence_insufficient=false when
    evidence_ids is empty.

13. Directly address the reasoning of the Bull claim.

14. Consider alternative interpretations,
    uncertainty, missing data, stale data,
    contradictory evidence, and downside risks.

15. Do not simply repeat the Risk Agent.

16. Do not promise future price declines.

17. Do not provide buy or sell advice.

18. Put important unresolved disputes or missing
    information into unresolved_questions.

19. Keep each counter_argument concise.
    Prefer approximately 2 to 4 sentences.

20. Do not repeat the full Bull claim inside the
    counter_argument.

21. Keep unresolved_questions concise.

22. Do not repeat the same objection in multiple
    rebuttals unless it is directly relevant.

23. Prefer precise evidence-grounded reasoning over
    long explanations.

24. Output only data matching the required schema.
""".strip()

        result, llm_call = self._llm.generate_structured(
            instructions=instructions,
            input_text=input_text,
            schema=BearCase,
            schema_name="bear_case",
        )

        self._validate_bull_claim_coverage(
            result,
            bull_case,
        )

        self._validate_evidence_ids(
            result,
            allowed_evidence_ids,
        )

        return BearExecution(
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
    def _validate_bull_claim_coverage(
        result: BearCase,
        bull_case: BullCase,
    ) -> None:
        bull_claim_ids = {claim.claim_id for claim in bull_case.claims}

        rebutted_ids = [rebuttal.bull_claim_id for rebuttal in result.rebuttals]

        if len(rebutted_ids) != len(set(rebutted_ids)):
            raise ValueError("Bear Agent rebutted the same Bull claim more than once.")

        if set(rebutted_ids) != bull_claim_ids:
            raise ValueError("Bear Agent must rebut every Bull claim exactly once.")

    @staticmethod
    def _validate_evidence_ids(
        result: BearCase,
        allowed_evidence_ids: set[str],
    ) -> None:
        for rebuttal in result.rebuttals:
            unknown_ids = set(rebuttal.evidence_ids) - allowed_evidence_ids

            if unknown_ids:
                raise ValueError(
                    f"Bear Agent returned unknown evidence IDs: {sorted(unknown_ids)}"
                )
