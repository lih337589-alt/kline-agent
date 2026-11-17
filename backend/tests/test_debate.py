import pytest
from pydantic import ValidationError

from app.schemas.debate import (
    BearRebuttal,
    BullClaim,
    DebateResult,
)


def test_bull_claim_normalizes_missing_evidence():
    claim = BullClaim(
        claim_id="bull-1",
        claim="Test claim",
        rationale="Test rationale",
        evidence_ids=[],
        evidence_insufficient=False,
    )

    assert claim.evidence_ids == []
    assert claim.evidence_insufficient is True


def test_bull_claim_normalizes_present_evidence():
    claim = BullClaim(
        claim_id="bull-1",
        claim="Test claim",
        rationale="Test rationale",
        evidence_ids=["financial:1"],
        evidence_insufficient=True,
    )

    assert claim.evidence_ids == ["financial:1"]

    assert claim.evidence_insufficient is False


def test_debate_requires_each_bull_claim_to_be_rebutted():
    bull_claims = [
        BullClaim(
            claim_id="bull-1",
            claim="Claim one",
            rationale="Reason one",
            evidence_ids=["financial:1"],
        ),
        BullClaim(
            claim_id="bull-2",
            claim="Claim two",
            rationale="Reason two",
            evidence_ids=["price:105"],
        ),
    ]

    bear_rebuttals = [
        BearRebuttal(
            rebuttal_id="bear-1",
            bull_claim_id="bull-1",
            counter_argument="Counter one",
            evidence_ids=["financial:1"],
        )
    ]

    with pytest.raises(ValidationError):
        DebateResult(
            bull_claims=bull_claims,
            bear_rebuttals=bear_rebuttals,
            unresolved_questions=[],
        )
