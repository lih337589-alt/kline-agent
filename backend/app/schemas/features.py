from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TechnicalFeatures(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    symbol: str
    as_of: datetime | None = None

    latest_close: float | None = None

    return_1d_pct: float | None = None
    return_5d_pct: float | None = None
    return_20d_pct: float | None = None

    sma_5: float | None = None
    sma_20: float | None = None

    volatility_20d_pct: float | None = None

    average_volume_5d: float | None = None
    average_volume_20d: float | None = None
    volume_ratio_5d_20d: float | None = None

    price_points_used: int = 0

    source_id: str | None = None


class ValuationFeatures(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    symbol: str

    latest_close: float | None = None

    period_end: str | None = None

    eps: float | None = None
    roe: float | None = None

    revenue: float | None = None
    net_income: float | None = None
    operating_cash_flow: float | None = None

    pe_ratio: float | None = None

    net_margin_pct: float | None = None
    operating_cash_flow_margin_pct: float | None = None

    missing_fields: list[str]

    price_source_id: str | None = None
    financial_source_id: str | None = None
