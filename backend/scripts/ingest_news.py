import argparse
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.providers.base import (
    ProviderError,
)
from app.data.providers.news_sample import (
    SampleNewsProvider,
)
from app.database.session import SessionLocal
from app.models import (
    Announcement,
    News,
    Stock,
)
from app.schemas.text import NormalizedText
from app.services.text_normalizer import (
    TextNormalizationError,
    make_title_hash,
    normalize_provider_record,
)


def get_stock(
    db: Session,
    symbol: str,
) -> Stock | None:
    statement = select(Stock).where(Stock.symbol == symbol.strip().upper())

    return db.scalar(statement)


def text_already_exists(
    db: Session,
    stock_id: int,
    item: NormalizedText,
) -> bool:
    if item.source_url:
        for model in (
            Announcement,
            News,
        ):
            statement = select(model).where(
                model.stock_id == stock_id,
                model.source_url == item.source_url,
            )

            if db.scalar(statement):
                return True

    for model in (
        Announcement,
        News,
    ):
        statement = select(model).where(
            model.stock_id == stock_id,
            model.published_at == item.published_at,
        )

        candidates = list(db.scalars(statement))

        for candidate in candidates:
            if make_title_hash(candidate.title) == item.title_hash:
                return True

    return False


def ingest_records(
    db: Session,
    stock: Stock,
    items: list[NormalizedText],
) -> tuple[int, int]:
    inserted = 0
    skipped = 0

    seen_urls: set[tuple[int, str]] = set()

    seen_title_times: set[tuple[int, str, datetime]] = set()

    for item in items:
        url_key = None

        if item.source_url:
            url_key = (
                stock.id,
                item.source_url,
            )

        title_time_key = (
            stock.id,
            item.title_hash,
            item.published_at,
        )

        duplicate_in_batch = (
            url_key is not None and url_key in seen_urls
        ) or title_time_key in seen_title_times

        if duplicate_in_batch:
            skipped += 1
            continue

        if text_already_exists(
            db,
            stock.id,
            item,
        ):
            if url_key is not None:
                seen_urls.add(url_key)

            seen_title_times.add(title_time_key)

            skipped += 1
            continue

        values = {
            "stock_id": stock.id,
            "title": item.title,
            "content": item.content,
            "source": item.source,
            "source_url": item.source_url,
            "published_at": (item.published_at),
        }

        if item.category == "announcement":
            db.add(Announcement(**values))
        else:
            db.add(News(**values))

        if url_key is not None:
            seen_urls.add(url_key)

        seen_title_times.add(title_time_key)

        inserted += 1

    return inserted, skipped


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--symbol",
        default="AAPL",
    )

    parser.add_argument(
        "--csv",
        default=("tests/fixtures/day9_texts.csv"),
    )

    args = parser.parse_args()

    symbol = args.symbol.strip().upper()

    provider = SampleNewsProvider(args.csv)

    try:
        records = provider.get_news(symbol)

        normalized_items = [normalize_provider_record(record) for record in records]

    except (
        ProviderError,
        TextNormalizationError,
    ) as exc:
        print(f"status=error symbol={symbol} reason={exc}")
        raise SystemExit(1) from exc

    with SessionLocal() as db:
        stock = get_stock(
            db,
            symbol,
        )

        if stock is None:
            print(f"status=error symbol={symbol} reason=stock_not_found")
            raise SystemExit(2)

        try:
            inserted, skipped = ingest_records(
                db,
                stock,
                normalized_items,
            )

            db.commit()

        except Exception:
            db.rollback()
            raise

    print(
        "status=ok "
        f"symbol={symbol} "
        f"fetched={len(records)} "
        f"inserted={inserted} "
        f"skipped={skipped}"
    )


if __name__ == "__main__":
    main()
