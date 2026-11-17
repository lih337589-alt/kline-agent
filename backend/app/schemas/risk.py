from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.context import ContextTextEvidence

RiskSeverity = Literal[
    "low",
    "medium",
    "high",
]


class FeatureSnapshot(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    symbol: str = Field(
        min_length=1,
        max_length=32,
    )

    timestamp: datetime

    price: float = Field(
        gt=0.0,
    )

    volume: int = Field(
        ge=0,
    )

    return_1m: float | None = None

    price_jump_pct: float | None = None

    volume_ratio: float | None = None

    sample_count: int = Field(
        ge=1,
    )


class RuleHit(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    rule_name: str = Field(
        min_length=1,
        max_length=64,
    )

    severity: RiskSeverity

    message: str = Field(
        min_length=1,
    )

    observed_value: float

    threshold: float


class RiskEventPackage(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    symbol: str = Field(
        min_length=1,
        max_length=32,
    )

    company_name: str = Field(
        min_length=1,
    )

    event_time: datetime

    alert_type: str = Field(
        min_length=1,
        max_length=64,
    )

    severity: RiskSeverity

    message: str = Field(
        min_length=1,
    )

    price: float = Field(
        gt=0.0,
    )

    volume: int = Field(
        ge=0,
    )

    return_1m: float | None = None

    price_jump_pct: float | None = None

    volume_ratio: float | None = None

    observed_value: float

    threshold: float

    recent_events: list[ContextTextEvidence] = Field(
        default_factory=list,
        max_length=3,
    )


class RiskExplanation(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    severity: RiskSeverity

    reason: str = Field(
        min_length=1,
    )

    impact_path: list[str] = Field(
        min_length=1,
        max_length=4,
    )

    uncertainty: str = Field(
        min_length=1,
    )

    suggested_attention: list[str] = Field(
        min_length=1,
        max_length=4,
    )


class RiskAlertRead(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    id: int

    stock_id: int

    symbol: str

    alert_type: str

    severity: RiskSeverity

    message: str

    source: str

    event_time: datetime

    created_at: datetime

    explanation: RiskExplanation | None = None


class RiskAlertListResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    count: int = Field(
        ge=0,
    )

    alerts: list[RiskAlertRead]
