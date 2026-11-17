import pytest
from pydantic import ValidationError

from app.schemas.review import (
    CrossExamResult,
    CrossIssue,
    JudgePointAssessment,
    JudgeResult,
)


def test_cross_issue_normalizes_missing_evidence():
    issue = CrossIssue(
        issue_id="cross-1",
        category="evidence_gap",
        severity="high",
        description="Missing evidence.",
        related_ids=["bull-1"],
        evidence_ids=[],
        evidence_insufficient=False,
    )

    assert issue.evidence_insufficient is True


def test_cross_exam_rejects_duplicate_issue_ids():
    issue = CrossIssue(
        issue_id="cross-1",
        category="data_quality",
        severity="medium",
        description="Synthetic evidence.",
        related_ids=["sentiment"],
        evidence_ids=[],
        evidence_insufficient=True,
    )

    with pytest.raises(ValidationError):
        CrossExamResult(
            summary="Test summary.",
            issues=[issue, issue],
            unresolved_questions=[],
        )


def test_judge_assessment_normalizes_present_evidence():
    assessment = JudgePointAssessment(
        point_id="bull-1",
        decision="uncertain",
        reason="Limited evidence.",
        evidence_ids=["financial:1"],
        evidence_insufficient=True,
    )

    assert assessment.evidence_insufficient is False


def test_judge_result_accepts_valid_assessment():
    result = JudgeResult(
        overall_view="Evidence is mixed.",
        key_drivers=[
            "Profitability",
        ],
        key_risks=[
            "Valuation",
        ],
        disputes=[
            "Trend durability",
        ],
        point_assessments=[
            JudgePointAssessment(
                point_id="bull-1",
                decision="uncertain",
                reason=("The supplied evidence is insufficient."),
                evidence_ids=[],
                evidence_insufficient=True,
            )
        ],
        confidence=0.4,
        data_freshness=("The supplied evidence is mixed."),
        limitations=[
            "Limited historical data.",
        ],
    )

    assert result.confidence == 0.4
