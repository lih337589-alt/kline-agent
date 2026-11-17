import json

from app.agents.base import (
    AgentExecution,
    EvidenceValidationError,
)
from app.llm.client import LLMClient
from app.schemas.agent import AgentResult
from app.schemas.context import AnalysisContext

_SENTIMENT_INSTRUCTIONS = """
You are the Sentiment Agent in a financial
research system.

Your task is to analyze recent company events,
announcements, and news using ONLY the evidence
provided in the input.

Strict rules:

1. Never invent facts, events, sources, URLs,
   or evidence IDs.

2. The only valid evidence IDs are the exact
   strings listed in allowed_evidence_ids.

3. When citing evidence, copy the evidence_id
   exactly. Do not modify it, abbreviate it,
   infer a new ID, or create a new ID.

4. If allowed_evidence_ids is empty, return:
   - evidence_ids as an empty list
   - a clear limitation saying that no recent
     event evidence is available.

5. positives must contain only materially
   positive event or sentiment signals supported
   by supplied evidence.

6. negatives must contain only materially
   negative event or sentiment signals supported
   by supplied evidence.

7. summary should describe the overall event
   sentiment and importance.

8. If the supplied evidence is sparse,
   conflicting, stale, or insufficient, state
   that clearly in limitations.

9. Do not calculate technical indicators or
   valuation metrics.

10. Do not make a price prediction.

11. Do not issue a buy or sell instruction.

12. confidence must be between 0 and 1.

13. Keep the response concise and professional.
""".strip()


class SentimentAgent:
    name = "sentiment"

    def __init__(
        self,
        llm_client: LLMClient,
    ) -> None:
        self.llm_client = llm_client

    def run(
        self,
        context: AnalysisContext,
    ) -> AgentExecution:
        evidence_catalog = [
            {
                "evidence_id": (item.source_ref.source_id),
                "category": item.category,
                "title": item.title,
                "content": item.content,
                "source": (item.source_ref.source),
                "source_url": (item.source_ref.source_url),
                "time": (item.source_ref.time.isoformat()),
            }
            for item in context.texts
        ]

        allowed_evidence_ids = {item["evidence_id"] for item in evidence_catalog}

        payload = {
            "symbol": context.symbol,
            "company_name": (context.company_name),
            "allowed_evidence_ids": sorted(allowed_evidence_ids),
            "evidence_catalog": (evidence_catalog),
        }

        result, call_info = self.llm_client.generate_structured(
            instructions=(_SENTIMENT_INSTRUCTIONS),
            input_text=json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            schema=AgentResult,
            schema_name=("sentiment_agent_result"),
        )

        self._validate_evidence_ids(
            result,
            allowed_evidence_ids,
        )

        return AgentExecution(
            agent_name=self.name,
            result=result,
            llm_call=call_info,
        )

    @staticmethod
    def _validate_evidence_ids(
        result: AgentResult,
        allowed_evidence_ids: set[str],
    ) -> None:
        invalid_ids = set(result.evidence_ids) - allowed_evidence_ids

        if invalid_ids:
            invalid = ", ".join(sorted(invalid_ids))

            raise EvidenceValidationError(
                "Sentiment agent returned "
                "evidence IDs not present "
                "in context: "
                f"{invalid}"
            )
