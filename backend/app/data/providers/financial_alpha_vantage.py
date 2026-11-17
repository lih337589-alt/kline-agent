import numpy as np
import pandas as pd

from app.data.providers.alpha_vantage_common import (
    AlphaVantageClient,
)
from app.data.providers.base import (
    FinancialDataProvider,
    ProviderError,
    ProviderRecord,
)


class AlphaVantageFinancialProvider(FinancialDataProvider):
    source = "alpha_vantage"

    def __init__(
        self,
        client: AlphaVantageClient,
    ) -> None:
        self.client = client

    def get_financial_data(
        self,
        symbol: str,
    ) -> list[ProviderRecord]:
        symbol = symbol.strip().upper()

        income_payload = self.client.get(
            function="INCOME_STATEMENT",
            symbol=symbol,
        )

        cash_payload = self.client.get(
            function="CASH_FLOW",
            symbol=symbol,
        )

        balance_payload = self.client.get(
            function="BALANCE_SHEET",
            symbol=symbol,
        )

        earnings_payload = self.client.get(
            function="EARNINGS",
            symbol=symbol,
        )

        income = _annual_frame(
            income_payload,
            root_key="annualReports",
            field_map={
                "totalRevenue": "revenue",
                "netIncome": "net_income",
            },
        )

        if income.empty:
            raise ProviderError(f"No annual income statement data found for {symbol}.")

        cash = _annual_frame(
            cash_payload,
            root_key="annualReports",
            field_map={
                "operatingCashflow": "operating_cash_flow",
            },
        )

        balance = _annual_frame(
            balance_payload,
            root_key="annualReports",
            field_map={
                "totalShareholderEquity": "shareholder_equity",
            },
        )

        earnings = _annual_frame(
            earnings_payload,
            root_key="annualEarnings",
            field_map={
                "reportedEPS": "eps",
            },
        )

        frame = income.merge(
            cash,
            on="period_end",
            how="left",
        )

        frame = frame.merge(
            balance,
            on="period_end",
            how="left",
        )

        frame = frame.merge(
            earnings,
            on="period_end",
            how="left",
        )

        numeric_columns = [
            "revenue",
            "net_income",
            "operating_cash_flow",
            "shareholder_equity",
            "eps",
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

        frame["period_end"] = pd.to_datetime(
            frame["period_end"],
            utc=True,
            errors="coerce",
        )

        frame = frame.dropna(subset=["period_end"])

        valid_roe = (
            frame["net_income"].notna()
            & frame["shareholder_equity"].notna()
            & (frame["shareholder_equity"] != 0)
        )

        frame["roe"] = np.nan

        frame.loc[
            valid_roe,
            "roe",
        ] = (
            frame.loc[
                valid_roe,
                "net_income",
            ]
            / frame.loc[
                valid_roe,
                "shareholder_equity",
            ]
        )

        frame = frame.sort_values("period_end")

        records: list[ProviderRecord] = []

        for row in frame.itertuples(index=False):
            records.append(
                ProviderRecord(
                    timestamp=(row.period_end.to_pydatetime()),
                    symbol=symbol,
                    source=self.source,
                    value={
                        "period_type": "annual",
                        "revenue": _optional_float(row.revenue),
                        "net_income": _optional_float(row.net_income),
                        "eps": _optional_float(row.eps),
                        "roe": _optional_float(row.roe),
                        "operating_cash_flow": _optional_float(row.operating_cash_flow),
                    },
                )
            )

        return records


def _annual_frame(
    payload: dict,
    *,
    root_key: str,
    field_map: dict[str, str],
) -> pd.DataFrame:
    reports = payload.get(root_key)

    output_columns = [
        "period_end",
        *field_map.values(),
    ]

    if not isinstance(reports, list):
        return pd.DataFrame(columns=output_columns)

    frame = pd.DataFrame(reports)

    if frame.empty:
        return pd.DataFrame(columns=output_columns)

    if "fiscalDateEnding" not in frame:
        raise ProviderError(f"{root_key} is missing fiscalDateEnding.")

    frame = frame.rename(
        columns={
            "fiscalDateEnding": "period_end",
            **field_map,
        }
    )

    for column in output_columns:
        if column not in frame:
            frame[column] = pd.NA

    return frame[output_columns]


def _optional_float(
    value: object,
) -> float | None:
    if pd.isna(value):
        return None

    return float(value)
