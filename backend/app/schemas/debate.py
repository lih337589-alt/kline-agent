from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BullClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(
        min_length=1,
        max_length=64,
    )

    claim: str = Field(
        min_length=1,
        max_length=1000,
    )

    rationale: str = Field(
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


class BullCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall_thesis: str = Field(
        min_length=1,
        max_length=1500,
    )

    claims: list[BullClaim] = Field(
        min_length=1,
        max_length=5,
    )

    @model_validator(mode="after")
    def validate_unique_claim_ids(
        self,
    ) -> "BullCase":
        claim_ids = [claim.claim_id for claim in self.claims]

        if len(claim_ids) != len(set(claim_ids)):
            raise ValueError("Bull claim_id values must be unique.")

        return self


class BearRebuttal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rebuttal_id: str = Field(
        min_length=1,
        max_length=64,
    )

    bull_claim_id: str = Field(
        min_length=1,
        max_length=64,
    )

    counter_argument: str = Field(
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


class BearCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rebuttals: list[BearRebuttal] = Field(
        min_length=1,
        max_length=5,
    )

    unresolved_questions: list[str] = Field(
        default_factory=list,
        max_length=10,
    )

    @model_validator(mode="after")
    def validate_unique_rebuttal_ids(
        self,
    ) -> "BearCase":
        rebuttal_ids = [rebuttal.rebuttal_id for rebuttal in self.rebuttals]

        if len(rebuttal_ids) != len(set(rebuttal_ids)):
            raise ValueError("Bear rebuttal_id values must be unique.")

        return self


class DebateResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bull_claims: list[BullClaim]
    bear_rebuttals: list[BearRebuttal]
    unresolved_questions: list[str]

    @model_validator(mode="after")
    def validate_rebuttal_coverage(
        self,
    ) -> "DebateResult":
        bull_ids = [claim.claim_id for claim in self.bull_claims]

        rebutted_ids = [rebuttal.bull_claim_id for rebuttal in self.bear_rebuttals]

        if len(rebutted_ids) != len(set(rebutted_ids)):
            raise ValueError("Each bull claim may be rebutted only once.")

        if set(bull_ids) != set(rebutted_ids):
            raise ValueError("Bear must rebut every bull claim exactly once.")

        return self
