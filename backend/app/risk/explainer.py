import json

from app.llm.client import (
    LLMCallInfo,
    LLMClient,
)
from app.schemas.context import (
    AnalysisContext,
)
from app.schemas.risk import (
    FeatureSnapshot,
    RiskEventPackage,
    RiskExplanation,
    RuleHit,
)

RISK_CONTEXT_EVENT_LIMIT = 3


_RISK_EXPLAINER_INSTRUCTIONS = """
You are the realtime Risk Explainer in a financial
research system.

A deterministic rule engine has already detected
the risk event. The supplied alert type, severity,
observed values, thresholds, prices, volumes, and
timestamps are authoritative system facts.

Your job is only to explain the alert clearly.

Rules:
1. Use only the supplied event package.
2. Never invent facts, metrics, news, events, or
   causes.
3. Do not change or recalculate the supplied
   observed values or thresholds.
4. Do not downgrade or upgrade the supplied
   severity.
5. If recent events do not establish a cause,
   explicitly state that causation is uncertain.
6. Do not make a price prediction.
7. Do not recommend buying, selling, holding,
   reducing, increasing, or otherwise changing a
   position.
8. suggested_attention must describe information
   the user may want to review or monitor, not a
   trading action.
9. impact_path must describe plausible risk
   transmission paths without presenting
   unsupported causation as fact.
10. Keep the explanation concise, factual, and
    professional.
""".strip()


class RiskExplainer:
    def __init__(
        self,
        llm_client: LLMClient,
    ) -> None:
        self.llm_client = llm_client

    def explain(
        self,
        event: RiskEventPackage,
    ) -> tuple[
        RiskExplanation,
        LLMCallInfo,
    ]:
        result, call_info = self.llm_client.generate_structured(
            instructions=(_RISK_EXPLAINER_INSTRUCTIONS),
            input_text=json.dumps(
                event.model_dump(
                    mode="json",
                ),
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            schema=RiskExplanation,
            schema_name=("risk_alert_explanation"),
        )

        if result.severity != event.severity:
            result = result.model_copy(
                update={
                    "severity": (event.severity),
                }
            )

        return (
            result,
            call_info,
        )


def build_risk_event_package(
    *,
    context: AnalysisContext,
    snapshot: FeatureSnapshot,
    rule_hit: RuleHit,
) -> RiskEventPackage:
    return RiskEventPackage(
        symbol=context.symbol,
        company_name=(context.company_name),
        event_time=(snapshot.timestamp),
        alert_type=(rule_hit.rule_name),
        severity=(rule_hit.severity),
        message=(rule_hit.message),
        price=snapshot.price,
        volume=snapshot.volume,
        return_1m=(snapshot.return_1m),
        price_jump_pct=(snapshot.price_jump_pct),
        volume_ratio=(snapshot.volume_ratio),
        observed_value=(rule_hit.observed_value),
        threshold=(rule_hit.threshold),
        recent_events=(context.texts[:RISK_CONTEXT_EVENT_LIMIT]),
    )
