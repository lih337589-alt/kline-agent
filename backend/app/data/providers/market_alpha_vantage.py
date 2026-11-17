from datetime import datetime

import numpy as np
import pandas as pd

from app.data.providers.alpha_vantage_common import (
    AlphaVantageClient,
)
from app.data.providers.base import (
    MarketDataProvider,
    ProviderError,
    ProviderRecord,
)


class AlphaVantageMarketProvider(MarketDataProvider):
    source = "alpha_vantage"

    def __init__(
        self,
        client: AlphaVantageClient,
    ) -> None:
        self.client = client

    def get_market_data(
        self,
        symbol: str,
    ) -> list[ProviderRecord]:
        symbol = symbol.strip().upper()

        data = self.client.get(
            function="TIME_SERIES_DAILY",
            symbol=symbol,
            extra_params={
                "outputsize": "compact",
            },
        )

        series = data.get("Time Series (Daily)")

        if not isinstance(series, dict):
            raise ProviderError(
                "TIME_SERIES_DAILY response does not contain daily data."
            )

        frame = pd.DataFrame.from_dict(
            series,
            orient="index",
        )

        required_columns = {
            "1. open",
            "2. high",
            "3. low",
            "4. close",
            "5. volume",
        }

        missing_columns = required_columns - set(frame.columns)

        if missing_columns:
            raise ProviderError(
                f"Market response is missing columns: {sorted(missing_columns)}"
            )

        frame = frame.rename(
            columns={
                "1. open": "open",
                "2. high": "high",
                "3. low": "low",
                "4. close": "close",
                "5. volume": "volume",
            }
        )

        frame.index.name = "timestamp"
        frame = frame.reset_index()

        frame["timestamp"] = pd.to_datetime(
            frame["timestamp"],
            utc=True,
            errors="coerce",
        )

        numeric_columns = [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]

        for column in numeric_columns:
            frame[column] = pd.to_numeric(
                frame[column],
                errors="coerce",
            )

        frame = frame.replace(
            [np.inf, -np.inf],
            np.nan,
        )

        frame = frame.dropna(
            subset=[
                "timestamp",
                "close",
            ]
        )

        frame = frame.sort_values("timestamp")

        records: list[ProviderRecord] = []

        for row in frame.itertuples(index=False):
            records.append(
                ProviderRecord(
                    timestamp=_to_datetime(row.timestamp),
                    symbol=symbol,
                    source=self.source,
                    value={
                        "open": _optional_float(row.open),
                        "high": _optional_float(row.high),
                        "low": _optional_float(row.low),
                        "close": float(row.close),
                        "volume": _optional_int(row.volume),
                    },
                )
            )

        return records


def _to_datetime(
    value: pd.Timestamp,
) -> datetime:
    return value.to_pydatetime()


def _optional_float(
    value: object,
) -> float | None:
    if pd.isna(value):
        return None

    return float(value)


def _optional_int(
    value: object,
) -> int | None:
    if pd.isna(value):
        return None

    return int(value)
