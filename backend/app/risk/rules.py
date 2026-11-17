from app.core.config import settings
from app.schemas.risk import (
    FeatureSnapshot,
    RuleHit,
)


class RiskRuleEngine:
    def __init__(
        self,
        *,
        return_threshold: float = (settings.risk_return_threshold),
        volume_ratio_threshold: float = (settings.risk_volume_ratio_threshold),
        price_jump_threshold: float = (settings.risk_price_jump_threshold),
    ) -> None:
        if return_threshold <= 0:
            raise ValueError("return_threshold must be positive")

        if volume_ratio_threshold <= 0:
            raise ValueError("volume_ratio_threshold must be positive")

        if price_jump_threshold <= 0:
            raise ValueError("price_jump_threshold must be positive")

        self.return_threshold = return_threshold

        self.volume_ratio_threshold = volume_ratio_threshold

        self.price_jump_threshold = price_jump_threshold

    def evaluate(
        self,
        snapshot: FeatureSnapshot,
    ) -> list[RuleHit]:
        hits: list[RuleHit] = []

        if snapshot.return_1m is not None:
            if snapshot.return_1m <= -self.return_threshold:
                hits.append(
                    RuleHit(
                        rule_name=("price_drop"),
                        severity="high",
                        message=(
                            f"{snapshot.symbol} "
                            "1-minute return "
                            f"{snapshot.return_1m:.2%} "
                            "crossed the downside "
                            f"threshold "
                            f"{-self.return_threshold:.2%}."
                        ),
                        observed_value=(snapshot.return_1m),
                        threshold=(-self.return_threshold),
                    )
                )

            if snapshot.return_1m >= self.return_threshold:
                hits.append(
                    RuleHit(
                        rule_name=("price_spike"),
                        severity="high",
                        message=(
                            f"{snapshot.symbol} "
                            "1-minute return "
                            f"{snapshot.return_1m:.2%} "
                            "crossed the upside "
                            f"threshold "
                            f"{self.return_threshold:.2%}."
                        ),
                        observed_value=(snapshot.return_1m),
                        threshold=(self.return_threshold),
                    )
                )

        if (
            snapshot.volume_ratio is not None
            and snapshot.volume_ratio >= self.volume_ratio_threshold
        ):
            hits.append(
                RuleHit(
                    rule_name=("volume_spike"),
                    severity="medium",
                    message=(
                        f"{snapshot.symbol} "
                        "volume ratio "
                        f"{snapshot.volume_ratio:.2f}x "
                        "crossed the threshold "
                        f"{self.volume_ratio_threshold:.2f}x."
                    ),
                    observed_value=(snapshot.volume_ratio),
                    threshold=(self.volume_ratio_threshold),
                )
            )

        if (
            snapshot.price_jump_pct is not None
            and abs(snapshot.price_jump_pct) >= self.price_jump_threshold
        ):
            hits.append(
                RuleHit(
                    rule_name=("price_jump"),
                    severity="medium",
                    message=(
                        f"{snapshot.symbol} "
                        "single-tick price move "
                        f"{snapshot.price_jump_pct:.2%} "
                        "crossed the absolute "
                        f"threshold "
                        f"{self.price_jump_threshold:.2%}."
                    ),
                    observed_value=(snapshot.price_jump_pct),
                    threshold=(self.price_jump_threshold),
                )
            )

        return hits
