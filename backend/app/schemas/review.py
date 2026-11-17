from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

CrossIssueCategory = Literal[
    "date_conflict",
    "evidence_gap",
    "logic_gap",
    "metric_mismatch",
    "data_quality",
    "other",
]

IssueSeverity = Literal[
    "low",
    "medium",
    "high",
]

JudgeDecision = Literal[
    "accepted",
    "rejected",
    "partially_accepted",
    "uncertain",
]


class CrossIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issue_id: str = Field(
        min_length=1,
        max_length=64,
    )

    category: CrossIssueCategory

    severity: IssueSeverity

    description: str = Field(
        min_length=1,
        max_length=1500,
    )

    related_ids: list[str] = Field(
        default_factory=list,
        max_length=10,
    )

    evidence_ids: list[str] = Field(
        default_factory=list,
        max_length=10,
    )

    evidence_insufficient: bool = False

    @model_validator(mode="before")
    @classmethod
    def normalize_evidence_status(
        cls,
        data: Any,
    ) -> Any:
        if not isinstance(data, dict):
            return data

        normalized = dict(data)

        evidence_ids = normalized.get(
            "evidence_ids",
            [],
        )

        normalized["evidence_insufficient"] = not bool(evidence_ids)

        return normalized


class CrossExamResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(
        min_length=1,
        max_length=2000,
    )

    issues: list[CrossIssue] = Field(
        default_factory=list,
        max_length=10,
    )

    unresolved_questions: list[str] = Field(
        default_factory=list,
        max_length=10,
    )

    @model_validator(mode="after")
    def validate_unique_issue_ids(
        self,
    ) -> "CrossExamResult":
        issue_ids = [issue.issue_id for issue in self.issues]

        if len(issue_ids) != len(set(issue_ids)):
            raise ValueError("Cross issue_id values must be unique.")

        return self


class JudgePointAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    point_id: str = Field(
        min_length=1,
        max_length=64,
    )

    decision: JudgeDecision

    reason: str = Field(
        min_length=1,
        max_length=1500,
    )

    evidence_ids: list[str] = Field(
        default_factory=list,
        max_length=10,
    )

    evidence_insufficient: bool = False

    @model_validator(mode="before")
    @classmethod
    def normalize_evidence_status(
        cls,
        data: Any,
    ) -> Any:
        if not isinstance(data, dict):
            return data

        normalized = dict(data)

        evidence_ids = normalized.get(
            "evidence_ids",
            [],
        )

        normalized["evidence_insufficient"] = not bool(evidence_ids)

        return normalized


class JudgeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall_view: str = Field(
        min_length=1,
        max_length=2500,
    )

    key_drivers: list[str] = Field(
        default_factory=list,
        max_length=8,
    )

    key_risks: list[str] = Field(
        default_factory=list,
        max_length=8,
    )

    disputes: list[str] = Field(
        default_factory=list,
        max_length=8,
    )

    point_assessments: list[JudgePointAssessment] = Field(
        min_length=1,
        max_length=20,
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    data_freshness: str = Field(
        min_length=1,
        max_length=1000,
    )

    limitations: list[str] = Field(
        default_factory=list,
        max_length=8,
    )

    @model_validator(mode="after")
    def validate_unique_assessments(
        self,
    ) -> "JudgeResult":
        point_ids = [item.point_id for item in self.point_assessments]

        if len(point_ids) != len(set(point_ids)):
            raise ValueError("Judge point assessments must use unique point_id values.")

        return self
