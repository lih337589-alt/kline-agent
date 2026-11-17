from pathlib import Path

import pandas as pd

from app.data.providers.base import (
    NewsProvider,
    ProviderError,
    ProviderRecord,
)

_REQUIRED_COLUMNS = {
    "published_at",
    "symbol",
    "source",
    "source_url",
    "category",
    "title",
    "content",
}


class SampleNewsProvider(NewsProvider):
    def __init__(
        self,
        csv_path: str | Path,
    ) -> None:
        self.csv_path = Path(csv_path)

    def get_news(
        self,
        symbol: str,
    ) -> list[ProviderRecord]:
        normalized_symbol = symbol.strip().upper()

        if not normalized_symbol:
            raise ProviderError("symbol cannot be empty")

        if not self.csv_path.exists():
            raise ProviderError(f"news sample file not found: {self.csv_path}")

        frame = pd.read_csv(self.csv_path)

        missing_columns = _REQUIRED_COLUMNS - set(frame.columns)

        if missing_columns:
            missing = ", ".join(sorted(missing_columns))

            raise ProviderError(f"news sample is missing columns: {missing}")

        frame["symbol"] = frame["symbol"].astype(str).str.strip().str.upper()

        frame = frame[frame["symbol"] == normalized_symbol].copy()

        frame["published_at"] = pd.to_datetime(
            frame["published_at"],
            utc=True,
            errors="coerce",
        )

        frame = frame.dropna(subset=["published_at"])

        frame = frame.sort_values("published_at")

        records: list[ProviderRecord] = []

        for _, row in frame.iterrows():
            source = _required_text(
                row["source"],
                "source",
            )

            title = _required_text(
                row["title"],
                "title",
            )

            records.append(
                ProviderRecord(
                    timestamp=row["published_at"].to_pydatetime(),
                    symbol=normalized_symbol,
                    source=source,
                    value={
                        "title": title,
                        "content": (_optional_text(row["content"]) or ""),
                        "source_url": (_optional_text(row["source_url"])),
                        "category": (
                            _required_text(
                                row["category"],
                                "category",
                            )
                        ),
                    },
                )
            )

        return records


def _optional_text(
    value: object,
) -> str | None:
    if pd.isna(value):
        return None

    text = str(value).strip()

    return text or None


def _required_text(
    value: object,
    field_name: str,
) -> str:
    text = _optional_text(value)

    if text is None:
        raise ProviderError(f"{field_name} cannot be empty")

    return text
