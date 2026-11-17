from types import SimpleNamespace

import pytest

from app.llm.client import (
    LLMClient,
    LLMLimitError,
)
from app.schemas.agent import AgentResult


def make_result() -> AgentResult:
    return AgentResult(
        summary="Test result",
        positives=[],
        negatives=[],
        evidence_ids=[],
        confidence=0.5,
        limitations=["Test limitation"],
    )


def make_client(
    *,
    max_calls: int = 5,
    max_input_chars: int = 20_000,
) -> LLMClient:
    return LLMClient(
        api_key="test-api-key",
        base_url=("https://example.invalid"),
        model="fake-model",
        timeout_seconds=1,
        max_retries=0,
        max_calls=max_calls,
        max_input_chars=max_input_chars,
    )


def install_fake_response(
    client: LLMClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = SimpleNamespace(
        output_text=(make_result().model_dump_json()),
        model="fake-model",
        id="fake-response-id",
        usage=SimpleNamespace(
            input_tokens=10,
            output_tokens=20,
            total_tokens=30,
        ),
    )

    def fake_create(
        **kwargs: object,
    ) -> object:
        return response

    monkeypatch.setattr(
        client.client.responses,
        "create",
        fake_create,
    )


def test_initial_call_count_is_zero() -> None:
    client = make_client()

    assert client.call_count == 0


def test_rejects_oversized_input() -> None:
    client = make_client(max_input_chars=10)

    with pytest.raises(
        LLMLimitError,
        match="character limit",
    ):
        client.generate_structured(
            instructions="12345",
            input_text="123456",
            schema=AgentResult,
            schema_name="test_result",
        )

    assert client.call_count == 0


def test_successful_call_increments_counter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = make_client(max_calls=2)

    install_fake_response(
        client,
        monkeypatch,
    )

    result, info = client.generate_structured(
        instructions="test",
        input_text="test",
        schema=AgentResult,
        schema_name="test_result",
    )

    assert result.summary == "Test result"

    assert info.total_tokens == 30

    assert client.call_count == 1


def test_call_limit_blocks_extra_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = make_client(max_calls=2)

    install_fake_response(
        client,
        monkeypatch,
    )

    for _ in range(2):
        client.generate_structured(
            instructions="test",
            input_text="test",
            schema=AgentResult,
            schema_name="test_result",
        )

    assert client.call_count == 2

    with pytest.raises(
        LLMLimitError,
        match="call limit",
    ):
        client.generate_structured(
            instructions="test",
            input_text="test",
            schema=AgentResult,
            schema_name="test_result",
        )

    assert client.call_count == 2
