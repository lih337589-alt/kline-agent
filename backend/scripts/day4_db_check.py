from sqlalchemy import select

from app.database.base import Base
from app.database.session import SessionLocal, engine
from app.models.stock import Stock

Base.metadata.create_all(bind=engine)


with SessionLocal() as session:
    stock = session.scalar(select(Stock).where(Stock.symbol == "TEST"))

    if stock is None:
        stock = Stock(
            symbol="TEST",
            name="Day 4 Test Company",
            exchange="TESTEX",
            industry="Technology",
        )

        session.add(stock)
        session.commit()
        session.refresh(stock)

        print("Created test stock:")
    else:
        print("Test stock already exists:")

    print(
        stock.id,
        stock.symbol,
        stock.name,
        stock.exchange,
        stock.industry,
    )
