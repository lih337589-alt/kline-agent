from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class SourceReference(BaseModel):
    source_id: str
    source: str
    source_url: str | None = None
    time: datetime


class MarketSnapshot(BaseModel):
    latest_close: float | None = None
    previous_close: float | None = None
    daily_return_pct: float | None = None
    five_day_return_pct: float | None = None
    average_volume_5d: float | None = None
    as_of: datetime | None = None
    price_points_used: int = 0
    source_ref: SourceReference | None = None


class FinancialEvidence(BaseModel):
    period_end: date
    period_type: str

    revenue: float | None = None
    net_income: float | None = None
    eps: float | None = None
    roe: float | None = None
    operating_cash_flow: float | None = None

    source_ref: SourceReference


class ContextTextEvidence(BaseModel):
    category: Literal[
        "announcement",
        "news",
        "research",
    ]

    title: str
    content: str

    source_ref: SourceReference


class AnalysisContext(BaseModel):
    symbol: str
    company_name: str

    built_at: datetime

    market: MarketSnapshot

    financials: list[FinancialEvidence]

    texts: list[ContextTextEvidence]
