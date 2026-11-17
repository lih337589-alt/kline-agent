from pydantic import BaseModel, ConfigDict, Field


class AgentResult(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    summary: str = Field(
        min_length=1,
        max_length=2000,
    )

    positives: list[str] = Field(
        max_length=5,
    )

    negatives: list[str] = Field(
        max_length=5,
    )

    evidence_ids: list[str] = Field(
        max_length=20,
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    limitations: list[str] = Field(
        max_length=5,
    )
