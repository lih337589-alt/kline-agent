from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func, select

from app.data.providers.base import (
    ProviderRecord,
)
from app.database.session import SessionLocal
from app.models import News, Stock
from app.services.text_normalizer import (
    normalize_provider_record,
)
from scripts.ingest_news import (
    ingest_records,
)


def test_news_ingestion_is_idempotent() -> None:
    symbol = "T" + uuid4().hex[:8].upper()

    with SessionLocal() as db:
        stock = Stock(
            symbol=symbol,
            name="Day 9 Test Stock",
            exchange="TEST",
            industry="Testing",
        )

        db.add(stock)
        db.commit()
        db.refresh(stock)

        try:
            record = ProviderRecord(
                timestamp=datetime(
                    2026,
                    9,
                    10,
                    12,
                    0,
                    tzinfo=timezone.utc,
                ),
                symbol=symbol,
                source="day9_test",
                value={
                    "title": ("Duplicate article"),
                    "content": ("Test content"),
                    "source_url": (f"https://example.test/{symbol}/news-001"),
                    "category": "news",
                },
            )

            item = normalize_provider_record(record)

            inserted, skipped = ingest_records(
                db,
                stock,
                [item, item],
            )

            db.commit()

            assert inserted == 1
            assert skipped == 1

            first_count = db.scalar(
                select(func.count(News.id)).where(News.stock_id == stock.id)
            )

            assert first_count == 1

            inserted, skipped = ingest_records(
                db,
                stock,
                [item],
            )

            db.commit()

            assert inserted == 0
            assert skipped == 1

            second_count = db.scalar(
                select(func.count(News.id)).where(News.stock_id == stock.id)
            )

            assert second_count == 1

        finally:
            db.delete(stock)
            db.commit()
