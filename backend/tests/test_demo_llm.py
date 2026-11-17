import json

from app.llm.demo import (
    DEMO_MODEL,
    DemoLLMClient,
)
from app.schemas.agent import AgentResult
from app.schemas.debate import (
    BearCase,
    BullCase,
)
from app.schemas.review import (
    CrossExamResult,
    JudgeResult,
)


def _input_text() -> str:
    return json.dumps(
        {
            "symbol": "AAPL",
            "allowed_evidence_ids": [
                "price:101",
                "financial:7",
                "news:9",
            ],
        }
    )


def test_demo_client_professional_agent() -> None:
    client = DemoLLMClient()

    result, info = client.generate_structured(
        instructions="test",
        input_text=_input_text(),
        schema=AgentResult,
        schema_name="fundamental_agent_result",
    )

    assert result.summary
    assert result.evidence_ids == [
        "financial:7",
        "news:9",
        "price:101",
    ]

    assert result.confidence == 0.6
    assert info.model == DEMO_MODEL
    assert client.call_count == 1


def test_demo_client_full_review_chain() -> None:
    client = DemoLLMClient()

    bull, _ = client.generate_structured(
        instructions="test",
        input_text=_input_text(),
        schema=BullCase,
        schema_name="bull_case",
    )

    assert len(bull.claims) == 1
    assert bull.claims[0].claim_id == "bull-1"

    bear_input = json.dumps(
        {
            "bull_case": bull.model_dump(mode="json"),
            "allowed_evidence_ids": [
                "price:101",
            ],
        }
    )

    bear, _ = client.generate_structured(
        instructions="test",
        input_text=bear_input,
        schema=BearCase,
        schema_name="bear_case",
    )

    assert len(bear.rebuttals) == 1
    assert bear.rebuttals[0].bull_claim_id == "bull-1"

    cross, _ = client.generate_structured(
        instructions="test",
        input_text=bear_input,
        schema=CrossExamResult,
        schema_name="cross_exam_result",
    )

    assert len(cross.issues) == 1
    assert cross.issues[0].issue_id == "cross-1"

    judge, _ = client.generate_structured(
        instructions="test",
        input_text=bear_input,
        schema=JudgeResult,
        schema_name="judge_result",
    )

    assert judge.overall_view
    assert judge.confidence == 0.5

    assert client.call_count == 4


def test_demo_client_extracts_only_evidence_ids() -> None:
    client = DemoLLMClient()

    result, _ = client.generate_structured(
        instructions="test",
        input_text=json.dumps(
            {
                "values": [
                    "price:123",
                    "financial:5",
                    "bull-1",
                    "random-value",
                ]
            }
        ),
        schema=AgentResult,
        schema_name="risk_agent_result",
    )

    assert result.evidence_ids == [
        "financial:5",
        "price:123",
    ]
