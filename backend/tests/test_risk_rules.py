from datetime import (
    datetime,
    timezone,
)

from app.risk.rules import (
    RiskRuleEngine,
)
from app.schemas.risk import (
    FeatureSnapshot,
)

NOW = datetime(
    2026,
    9,
    21,
    tzinfo=timezone.utc,
)


def make_snapshot(
    *,
    return_1m: float | None = None,
    price_jump_pct: float | None = None,
    volume_ratio: float | None = None,
) -> FeatureSnapshot:
    return FeatureSnapshot(
        symbol="AAPL",
        timestamp=NOW,
        price=100.0,
        volume=1_000,
        return_1m=return_1m,
        price_jump_pct=(price_jump_pct),
        volume_ratio=(volume_ratio),
        sample_count=2,
    )


def make_engine() -> RiskRuleEngine:
    return RiskRuleEngine(
        return_threshold=0.02,
        volume_ratio_threshold=2.5,
        price_jump_threshold=0.01,
    )


def test_normal_snapshot_has_no_rule_hits() -> None:
    hits = make_engine().evaluate(
        make_snapshot(
            return_1m=0.005,
            price_jump_pct=0.003,
            volume_ratio=1.2,
        )
    )

    assert hits == []


def test_price_drop_rule() -> None:
    hits = make_engine().evaluate(
        make_snapshot(
            return_1m=-0.02,
        )
    )

    assert [hit.rule_name for hit in hits] == ["price_drop"]

    assert hits[0].severity == "high"


def test_price_spike_rule() -> None:
    hits = make_engine().evaluate(
        make_snapshot(
            return_1m=0.02,
        )
    )

    assert [hit.rule_name for hit in hits] == ["price_spike"]


def test_volume_spike_rule() -> None:
    hits = make_engine().evaluate(
        make_snapshot(
            volume_ratio=2.5,
        )
    )

    assert [hit.rule_name for hit in hits] == ["volume_spike"]


def test_price_jump_rule_uses_absolute_value() -> None:
    positive = make_engine().evaluate(
        make_snapshot(
            price_jump_pct=0.01,
        )
    )

    negative = make_engine().evaluate(
        make_snapshot(
            price_jump_pct=-0.01,
        )
    )

    assert positive[0].rule_name == ("price_jump")

    assert negative[0].rule_name == ("price_jump")


def test_multiple_rules_can_fire() -> None:
    hits = make_engine().evaluate(
        make_snapshot(
            return_1m=-0.03,
            price_jump_pct=-0.015,
            volume_ratio=3.0,
        )
    )

    assert {hit.rule_name for hit in hits} == {
        "price_drop",
        "volume_spike",
        "price_jump",
    }


def test_missing_features_do_not_fire() -> None:
    hits = make_engine().evaluate(make_snapshot())

    assert hits == []
