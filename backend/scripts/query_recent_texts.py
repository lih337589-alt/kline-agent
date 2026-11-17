import argparse

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models import Stock
from app.services.text_evidence import (
    get_recent_text_evidence,
)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--symbol",
        default="AAPL",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=5,
    )

    args = parser.parse_args()

    symbol = args.symbol.strip().upper()

    if args.limit < 1:
        print("status=error reason=limit_must_be_positive")
        raise SystemExit(2)

    with SessionLocal() as db:
        stock = db.scalar(select(Stock).where(Stock.symbol == symbol))

        if stock is None:
            print(f"status=error symbol={symbol} reason=stock_not_found")
            raise SystemExit(2)

        evidence = get_recent_text_evidence(
            db,
            stock,
            args.limit,
        )

    print(f"status=ok symbol={symbol} count={len(evidence)}")

    for index, item in enumerate(
        evidence,
        start=1,
    ):
        print(
            f"{index}. "
            f"[{item.category}] "
            f"{item.published_at.isoformat()} "
            f"| {item.source} "
            f"| {item.title} "
            f"| {item.source_url or '-'}"
        )


if __name__ == "__main__":
    main()
