import json
from datetime import (
    datetime,
    timezone,
)

import pytest

from app.llm.client import (
    LLMCallInfo,
    LLMProviderError,
)
from app.risk.explainer import (
    RiskExplainer,
)
from app.schemas.risk import (
    RiskEventPackage,
    RiskExplanation,
)

NOW = datetime(
    2026,
    9,
    22,
    12,
    0,
    tzinfo=timezone.utc,
)


class FakeLLMClient:
    def __init__(
        self,
        *,
        result: (RiskExplanation | None) = None,
        error: (Exception | None) = None,
    ) -> None:
        self.result = result
        self.error = error
        self.call_count = 0
        self.last_input_text: str | None = None
        self.last_schema_name: str | None = None

    def generate_structured(
        self,
        **kwargs: object,
    ) -> tuple[
        RiskExplanation,
        LLMCallInfo,
    ]:
        self.call_count += 1

        input_text = kwargs.get("input_text")

        schema_name = kwargs.get("schema_name")

        if isinstance(
            input_text,
            str,
        ):
            self.last_input_text = input_text

        if isinstance(
            schema_name,
            str,
        ):
            self.last_schema_name = schema_name

        if self.error is not None:
            raise self.error

        assert self.result is not None

        return (
            self.result,
            LLMCallInfo(
                model="fake-model",
                elapsed_ms=1,
                input_tokens=10,
                output_tokens=20,
                total_tokens=30,
            ),
        )


def make_event() -> RiskEventPackage:
    return RiskEventPackage(
        symbol="AAPL",
        company_name="Apple Test",
        event_time=NOW,
        alert_type="price_drop",
        severity="high",
        message=("AAPL 1-minute return -3.00% crossed the downside threshold -2.00%."),
        price=97.0,
        volume=1_000,
        return_1m=-0.03,
        price_jump_pct=-0.03,
        volume_ratio=1.0,
        observed_value=-0.03,
        threshold=-0.02,
        recent_events=[],
    )


def test_risk_explainer_returns_structured_result() -> None:
    expected = RiskExplanation(
        severity="high",
        reason=("The short-term decline crossed the configured risk threshold."),
        impact_path=[
            "Rapid downside move",
            "Higher short-term volatility",
        ],
        uncertainty=("No supplied event evidence establishes the cause."),
        suggested_attention=[
            "Check whether the move persists",
            "Review recent company events",
        ],
    )

    fake = FakeLLMClient(
        result=expected,
    )

    result, call_info = RiskExplainer(fake).explain(make_event())

    assert result == expected
    assert call_info.total_tokens == 30

    assert fake.call_count == 1

    assert fake.last_schema_name == "risk_alert_explanation"

    assert fake.last_input_text is not None

    payload = json.loads(fake.last_input_text)

    assert payload["symbol"] == "AAPL"

    assert payload["observed_value"] == -0.03

    assert payload["threshold"] == -0.02


def test_risk_explainer_preserves_rule_severity() -> None:
    fake = FakeLLMClient(
        result=RiskExplanation(
            severity="low",
            reason="Test reason.",
            impact_path=["Test path"],
            uncertainty=("Test uncertainty."),
            suggested_attention=["Review the event"],
        ),
    )

    result, _ = RiskExplainer(fake).explain(make_event())

    assert result.severity == "high"


def test_risk_explainer_propagates_provider_failure() -> None:
    fake = FakeLLMClient(
        error=LLMProviderError("provider unavailable"),
    )

    with pytest.raises(
        LLMProviderError,
    ):
        RiskExplainer(fake).explain(make_event())
