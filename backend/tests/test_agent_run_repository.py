from uuid import uuid4

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.agent_run import AgentRun
from app.models.stock import Stock
from app.repositories.agent_run import (
    create_agent_run,
)


def test_create_agent_run() -> None:
    symbol = "T" + uuid4().hex[:8].upper()

    trace_id = uuid4().hex

    with SessionLocal() as db:
        stock = Stock(
            symbol=symbol,
            name="Agent Run Test Stock",
            exchange="TEST",
            industry="Testing",
        )

        db.add(stock)
        db.commit()
        db.refresh(stock)

        try:
            agent_run = create_agent_run(
                db,
                stock_id=stock.id,
                trace_id=trace_id,
                agent_type="fundamental",
                model_name=("fake-deepseek-model"),
                status="success",
                input_summary=('{"symbol":"TEST"}'),
                output_json=('{"summary":"test"}'),
                error_message=None,
                duration_ms=123,
                token_count=42,
                source="deepseek",
            )

            agent_run_id = agent_run.id

            db.commit()

            stored = db.scalar(select(AgentRun).where(AgentRun.id == agent_run_id))

            assert stored is not None

            assert stored.stock_id == stock.id

            assert stored.trace_id == trace_id

            assert stored.agent_type == "fundamental"

            assert stored.status == "success"

            assert stored.duration_ms == 123

            assert stored.token_count == 42

            assert stored.source == "deepseek"

        finally:
            db.delete(stock)
            db.commit()
