from pathlib import Path

import pandas as pd

from app.data.providers.base import (
    FinancialDataProvider,
    MarketDataProvider,
    NewsProvider,
    ProviderRecord,
)


class MockProvider(
    MarketDataProvider,
    FinancialDataProvider,
    NewsProvider,
):
    def __init__(
        self,
        fixture_dir: Path,
    ) -> None:
        self.fixture_dir = fixture_dir

    def _read_csv(
        self,
        filename: str,
    ) -> pd.DataFrame:
        path = self.fixture_dir / filename

        if not path.exists():
            raise FileNotFoundError(f"Fixture not found: {path}")

        return pd.read_csv(path)

    @staticmethod
    def _normalize_symbol(
        symbol: str,
    ) -> str:
        return symbol.strip().upper()

    @staticmethod
    def _parse_timestamp(
        value: str,
    ):
        return pd.to_datetime(
            value,
            utc=True,
        ).to_pydatetime()

    def get_market_data(
        self,
        symbol: str,
    ) -> list[ProviderRecord]:
        frame = self._read_csv("market.csv")

        target = self._normalize_symbol(symbol)

        frame = frame[frame["symbol"].astype(str).str.upper() == target]

        records: list[ProviderRecord] = []

        for row in frame.itertuples(index=False):
            records.append(
                ProviderRecord(
                    timestamp=self._parse_timestamp(row.timestamp),
                    symbol=str(row.symbol).upper(),
                    source=str(row.source),
                    value={
                        "open": float(row.open),
                        "high": float(row.high),
                        "low": float(row.low),
                        "close": float(row.close),
                        "volume": int(row.volume),
                    },
                )
            )

        return records

    def get_financial_data(
        self,
        symbol: str,
    ) -> list[ProviderRecord]:
        frame = self._read_csv("financial.csv")

        target = self._normalize_symbol(symbol)

        frame = frame[frame["symbol"].astype(str).str.upper() == target]

        records: list[ProviderRecord] = []

        for row in frame.itertuples(index=False):
            records.append(
                ProviderRecord(
                    timestamp=self._parse_timestamp(row.timestamp),
                    symbol=str(row.symbol).upper(),
                    source=str(row.source),
                    value={
                        "period_type": str(row.period_type),
                        "revenue": float(row.revenue),
                        "net_income": float(row.net_income),
                        "eps": float(row.eps),
                        "roe": float(row.roe),
                        "operating_cash_flow": float(row.operating_cash_flow),
                    },
                )
            )

        return records

    def get_news(
        self,
        symbol: str,
    ) -> list[ProviderRecord]:
        frame = self._read_csv("news.csv")

        target = self._normalize_symbol(symbol)

        frame = frame[frame["symbol"].astype(str).str.upper() == target]

        records: list[ProviderRecord] = []

        for row in frame.itertuples(index=False):
            records.append(
                ProviderRecord(
                    timestamp=self._parse_timestamp(row.timestamp),
                    symbol=str(row.symbol).upper(),
                    source=str(row.source),
                    value={
                        "title": str(row.title),
                        "content": str(row.content),
                        "source_url": str(row.source_url),
                    },
                )
            )

        return records
