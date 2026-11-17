from datetime import (
    date,
    datetime,
    timedelta,
    timezone,
)
from decimal import Decimal
from uuid import uuid4

from app.database.session import SessionLocal
from app.models.financial import Financial
from app.models.price import Price
from app.models.stock import Stock
from app.services.feature_engineering import (
    build_technical_features,
    build_valuation_features,
)


def test_technical_features_are_deterministic() -> None:
    symbol = "T" + uuid4().hex[:8].upper()

    with SessionLocal() as db:
        stock = Stock(
            symbol=symbol,
            name="Technical Test Stock",
            exchange="TEST",
            industry="Testing",
        )

        db.add(stock)
        db.commit()
        db.refresh(stock)

        try:
            start = datetime(
                2026,
                1,
                1,
                tzinfo=timezone.utc,
            )

            for index in range(21):
                db.add(
                    Price(
                        stock_id=stock.id,
                        timestamp=(start + timedelta(days=index)),
                        close=Decimal(str(100 + index)),
                        volume=(1000 + index),
                        source="test",
                    )
                )

            db.commit()

            features = build_technical_features(
                db,
                stock,
            )

            assert features.latest_close == 120.0

            assert features.return_1d_pct == 0.8403

            assert features.return_5d_pct == 4.3478

            assert features.return_20d_pct == 20.0

            assert features.sma_5 == 118.0

            assert features.sma_20 == 110.5

            assert features.volatility_20d_pct is not None

        finally:
            db.delete(stock)
            db.commit()


def test_valuation_features() -> None:
    symbol = "V" + uuid4().hex[:8].upper()

    with SessionLocal() as db:
        stock = Stock(
            symbol=symbol,
            name="Valuation Test Stock",
            exchange="TEST",
            industry="Testing",
        )

        db.add(stock)
        db.commit()
        db.refresh(stock)

        try:
            db.add(
                Price(
                    stock_id=stock.id,
                    timestamp=datetime(
                        2026,
                        1,
                        1,
                        tzinfo=timezone.utc,
                    ),
                    close=Decimal(100),
                    volume=1000,
                    source="test",
                )
            )

            db.add(
                Financial(
                    stock_id=stock.id,
                    period_end=date(
                        2025,
                        12,
                        31,
                    ),
                    period_type="annual",
                    revenue=Decimal(1000),
                    net_income=Decimal(100),
                    eps=Decimal(5),
                    roe=Decimal("0.20"),
                    operating_cash_flow=(Decimal(150)),
                    source="test",
                )
            )

            db.commit()

            features = build_valuation_features(
                db,
                stock,
            )

            assert features.latest_close == 100.0

            assert features.pe_ratio == 20.0

            assert features.net_margin_pct == 10.0

            assert features.operating_cash_flow_margin_pct == 15.0

            assert features.missing_fields == []

        finally:
            db.delete(stock)
            db.commit()
