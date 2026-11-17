import json
from dataclasses import dataclass

from app.agents.registry import AgentRunOutcome
from app.llm.client import LLMCallInfo, LLMClient
from app.schemas.debate import BullCase


@dataclass(frozen=True)
class BullExecution:
    result: BullCase
    llm_call: LLMCallInfo


class BullAgent:
    def __init__(self, llm_client: LLMClient) -> None:
        self._llm = llm_client

    def run(
        self,
        outcomes: list[AgentRunOutcome],
    ) -> BullExecution:
        allowed_evidence_ids = self._collect_evidence_ids(outcomes)

        input_text = json.dumps(
            {
                "professional_agent_results": (self._serialize_outcomes(outcomes)),
                "allowed_evidence_ids": sorted(allowed_evidence_ids),
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )

        instructions = """
You are the Bull Agent in an evidence-grounded
financial research debate.

Your task is to construct the strongest reasonable
bullish case using ONLY the supplied professional
agent results.

Rules:

1. Read all available professional-agent results.
2. Produce between 1 and 5 distinct bullish claims.
3. Give every claim a unique claim_id such as
   bull-1, bull-2, bull-3.
4. Every factual claim must cite evidence_ids copied
   exactly from allowed_evidence_ids.
5. Never invent an evidence ID.
6. If a claim cannot be supported by available
   evidence, evidence_ids must be empty and
   evidence_insufficient must be true.
7. Do not hide negative evidence.
8. Do not promise price appreciation.
9. Do not provide investment advice.
10. Focus on the strongest evidence-based bullish
    interpretation that a Bear Agent can challenge.
""".strip()

        result, llm_call = self._llm.generate_structured(
            instructions=instructions,
            input_text=input_text,
            schema=BullCase,
            schema_name="bull_case",
        )

        self._validate_evidence_ids(
            result,
            allowed_evidence_ids,
        )

        return BullExecution(
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
    def _validate_evidence_ids(
        result: BullCase,
        allowed_evidence_ids: set[str],
    ) -> None:
        for claim in result.claims:
            unknown_ids = set(claim.evidence_ids) - allowed_evidence_ids

            if unknown_ids:
                raise ValueError(
                    f"Bull Agent returned unknown evidence IDs: {sorted(unknown_ids)}"
                )
