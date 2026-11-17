from dataclasses import dataclass
from time import perf_counter
from typing import TypeVar

import openai
from openai import OpenAI
from pydantic import BaseModel, ValidationError

from app.core.limits import (
    LLM_MAX_CALLS_PER_ANALYSIS,
    LLM_MAX_INPUT_CHARS,
    LLM_MAX_OUTPUT_TOKENS,
    LLM_MAX_RETRIES,
)

T = TypeVar(
    "T",
    bound=BaseModel,
)


class LLMProviderError(RuntimeError):
    pass


class LLMOutputError(RuntimeError):
    pass


class LLMLimitError(ValueError):
    pass


@dataclass(frozen=True)
class LLMCallInfo:
    model: str
    elapsed_ms: int

    response_id: str | None = None
    request_id: str | None = None

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


class LLMClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float = 30.0,
        max_retries: int = LLM_MAX_RETRIES,
        max_calls: int = LLM_MAX_CALLS_PER_ANALYSIS,
        max_input_chars: int = LLM_MAX_INPUT_CHARS,
    ) -> None:
        if not api_key.strip():
            raise ValueError("LLM API key is not configured")

        if not base_url.strip():
            raise ValueError("LLM base URL is not configured")

        if not model.strip():
            raise ValueError("LLM model is not configured")

        if timeout_seconds <= 0:
            raise ValueError("LLM timeout must be positive")

        if max_retries < 0:
            raise ValueError("LLM max retries cannot be negative")

        if max_calls <= 0:
            raise ValueError("LLM max calls must be positive")

        if max_input_chars <= 0:
            raise ValueError("LLM max input chars must be positive")

        self.model = model.strip()
        self.max_calls = max_calls
        self.max_input_chars = max_input_chars

        self._call_count = 0

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout_seconds,
            max_retries=max_retries,
        )

    @property
    def call_count(self) -> int:
        return self._call_count

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

        started_at = perf_counter()

        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=instructions,
                input=input_text,
                reasoning={
                    "effort": "none",
                },
                max_output_tokens=(LLM_MAX_OUTPUT_TOKENS),
                text={
                    "format": {
                        "type": "json_schema",
                        "name": schema_name,
                        "schema": (schema.model_json_schema()),
                    }
                },
            )

        except openai.APIError as exc:
            raise LLMProviderError(f"LLM provider request failed: {exc}") from exc

        elapsed_ms = int((perf_counter() - started_at) * 1000)

        output_text = (response.output_text or "").strip()

        if not output_text:
            raise LLMOutputError("LLM returned empty output")

        try:
            parsed = schema.model_validate_json(output_text)

        except ValidationError as exc:
            validation_details = "; ".join(
                (f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}")
                for error in exc.errors()
            )

            raise LLMOutputError(
                f"LLM output failed Pydantic validation: {validation_details}"
            ) from exc

        usage = response.usage

        info = LLMCallInfo(
            model=str(response.model),
            elapsed_ms=elapsed_ms,
            response_id=getattr(
                response,
                "id",
                None,
            ),
            request_id=getattr(
                response,
                "_request_id",
                None,
            ),
            input_tokens=(
                getattr(
                    usage,
                    "input_tokens",
                    None,
                )
                if usage
                else None
            ),
            output_tokens=(
                getattr(
                    usage,
                    "output_tokens",
                    None,
                )
                if usage
                else None
            ),
            total_tokens=(
                getattr(
                    usage,
                    "total_tokens",
                    None,
                )
                if usage
                else None
            ),
        )

        return parsed, info

    def _check_input_length(
        self,
        *,
        instructions: str,
        input_text: str,
    ) -> None:
        input_chars = len(instructions) + len(input_text)

        if input_chars > self.max_input_chars:
            raise LLMLimitError(
                "LLM input exceeds character "
                "limit: "
                f"{input_chars} > "
                f"{self.max_input_chars}"
            )

    def _reserve_call(self) -> None:
        if self._call_count >= self.max_calls:
            raise LLMLimitError(f"LLM call limit exceeded: max_calls={self.max_calls}")

        self._call_count += 1
