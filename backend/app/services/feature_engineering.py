from math import sqrt
from statistics import mean, stdev

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.financial import Financial
from app.models.price import Price
from app.models.stock import Stock
from app.schemas.features import (
    TechnicalFeatures,
    ValuationFeatures,
)

PRICE_HISTORY_LIMIT = 60


def build_technical_features(
    db: Session,
    stock: Stock,
) -> TechnicalFeatures:
    prices = list(
        db.scalars(
            select(Price)
            .where(Price.stock_id == stock.id)
            .order_by(Price.timestamp.desc())
            .limit(PRICE_HISTORY_LIMIT)
        )
    )

    if not prices:
        return TechnicalFeatures(
            symbol=stock.symbol,
        )

    closes = [float(price.close) for price in prices if price.close is not None]

    latest = prices[0]

    latest_close = float(latest.close) if latest.close is not None else None

    return_1d_pct = _period_return(
        closes,
        periods=1,
    )

    return_5d_pct = _period_return(
        closes,
        periods=5,
    )

    return_20d_pct = _period_return(
        closes,
        periods=20,
    )

    sma_5 = _average(closes[:5])

    sma_20 = _average(closes[:20])

    volatility_20d_pct = _annualized_volatility(closes[:21])

    volumes = [
        float(price.volume) if price.volume is not None else None for price in prices
    ]

    average_volume_5d = _average_non_null(volumes[:5])

    average_volume_20d = _average_non_null(volumes[:20])

    volume_ratio = None

    if average_volume_5d is not None and average_volume_20d not in (None, 0):
        volume_ratio = round(
            average_volume_5d / average_volume_20d,
            4,
        )

    return TechnicalFeatures(
        symbol=stock.symbol,
        as_of=latest.timestamp,
        latest_close=latest_close,
        return_1d_pct=return_1d_pct,
        return_5d_pct=return_5d_pct,
        return_20d_pct=return_20d_pct,
        sma_5=sma_5,
        sma_20=sma_20,
        volatility_20d_pct=(volatility_20d_pct),
        average_volume_5d=(average_volume_5d),
        average_volume_20d=(average_volume_20d),
        volume_ratio_5d_20d=(volume_ratio),
        price_points_used=len(closes),
        source_id=(f"price:{latest.id}"),
    )


def build_valuation_features(
    db: Session,
    stock: Stock,
) -> ValuationFeatures:
    latest_price = db.scalar(
        select(Price)
        .where(Price.stock_id == stock.id)
        .order_by(Price.timestamp.desc())
        .limit(1)
    )

    latest_financial = db.scalar(
        select(Financial)
        .where(Financial.stock_id == stock.id)
        .order_by(Financial.period_end.desc())
        .limit(1)
    )

    latest_close = None

    price_source_id = None

    if latest_price is not None:
        latest_close = (
            float(latest_price.close) if latest_price.close is not None else None
        )

        price_source_id = f"price:{latest_price.id}"

    if latest_financial is None:
        return ValuationFeatures(
            symbol=stock.symbol,
            latest_close=latest_close,
            missing_fields=[
                "financials",
            ],
            price_source_id=(price_source_id),
        )

    eps = _to_float(latest_financial.eps)

    roe = _to_float(latest_financial.roe)

    revenue = _to_float(latest_financial.revenue)

    net_income = _to_float(latest_financial.net_income)

    operating_cash_flow = _to_float(latest_financial.operating_cash_flow)

    pe_ratio = None

    if latest_close is not None and eps is not None and eps > 0:
        pe_ratio = round(
            latest_close / eps,
            4,
        )

    net_margin_pct = _ratio_pct(
        net_income,
        revenue,
    )

    operating_cash_flow_margin_pct = _ratio_pct(
        operating_cash_flow,
        revenue,
    )

    missing_fields: list[str] = []

    values = {
        "latest_close": latest_close,
        "eps": eps,
        "roe": roe,
        "revenue": revenue,
        "net_income": net_income,
        "operating_cash_flow": (operating_cash_flow),
        "pe_ratio": pe_ratio,
    }

    for field_name, value in values.items():
        if value is None:
            missing_fields.append(field_name)

    return ValuationFeatures(
        symbol=stock.symbol,
        latest_close=latest_close,
        period_end=(latest_financial.period_end.isoformat()),
        eps=eps,
        roe=roe,
        revenue=revenue,
        net_income=net_income,
        operating_cash_flow=(operating_cash_flow),
        pe_ratio=pe_ratio,
        net_margin_pct=(net_margin_pct),
        operating_cash_flow_margin_pct=(operating_cash_flow_margin_pct),
        missing_fields=missing_fields,
        price_source_id=(price_source_id),
        financial_source_id=(f"financial:{latest_financial.id}"),
    )


def _period_return(
    closes: list[float],
    *,
    periods: int,
) -> float | None:
    if len(closes) <= periods:
        return None

    current = closes[0]
    previous = closes[periods]

    if previous == 0:
        return None

    return round(
        (current / previous - 1) * 100,
        4,
    )


def _average(
    values: list[float],
) -> float | None:
    if not values:
        return None

    return round(
        mean(values),
        4,
    )


def _average_non_null(
    values: list[float | None],
) -> float | None:
    cleaned = [value for value in values if value is not None]

    if not cleaned:
        return None

    return round(
        mean(cleaned),
        4,
    )


def _annualized_volatility(
    closes: list[float],
) -> float | None:
    if len(closes) < 3:
        return None

    chronological = list(reversed(closes))

    returns: list[float] = []

    for index in range(
        1,
        len(chronological),
    ):
        previous = chronological[index - 1]

        current = chronological[index]

        if previous == 0:
            continue

        returns.append(current / previous - 1)

    if len(returns) < 2:
        return None

    daily_volatility = stdev(returns)

    annualized = daily_volatility * sqrt(252) * 100

    return round(
        annualized,
        4,
    )


def _to_float(
    value: object,
) -> float | None:
    if value is None:
        return None

    return float(value)


def _ratio_pct(
    numerator: float | None,
    denominator: float | None,
) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None

    return round(
        numerator / denominator * 100,
        4,
    )
