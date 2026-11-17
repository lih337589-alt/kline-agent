from uuid import uuid4

from app.database.session import SessionLocal
from app.models.stock import Stock
from app.repositories.report import (
    create_report,
    get_report_by_id,
)


def test_create_and_get_report() -> None:
    symbol = "R" + uuid4().hex[:8].upper()

    trace_id = uuid4().hex

    with SessionLocal() as db:
        stock = Stock(
            symbol=symbol,
            name="Report Repository Test Stock",
            exchange="TEST",
            industry="Testing",
        )

        db.add(stock)
        db.commit()
        db.refresh(stock)

        try:
            report = create_report(
                db,
                stock_id=stock.id,
                trace_id=trace_id,
                title=(f"{symbol} Test Report"),
                report_json=('{"symbol":"' + symbol + '"}'),
                status="completed",
                source="test",
            )

            report_id = report.id

            db.commit()

            stored = get_report_by_id(
                db,
                report_id,
            )

            assert stored is not None
            assert stored.id == report_id
            assert stored.stock_id == stock.id
            assert stored.trace_id == trace_id
            assert stored.title == f"{symbol} Test Report"
            assert stored.status == "completed"
            assert stored.source == "test"
            assert stored.report_json == ('{"symbol":"' + symbol + '"}')

        finally:
            db.delete(stock)
            db.commit()


def test_get_missing_report_returns_none() -> None:
    with SessionLocal() as db:
        report = get_report_by_id(
            db,
            2_147_483_647,
        )

    assert report is None
