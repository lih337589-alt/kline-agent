from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Financial(Base):
    __tablename__ = "financials"

    id: Mapped[int] = mapped_column(primary_key=True)

    stock_id: Mapped[int] = mapped_column(
        ForeignKey("stocks.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    period_end: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    period_type: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )

    revenue: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 2),
        nullable=True,
    )

    net_income: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 2),
        nullable=True,
    )

    eps: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 6),
        nullable=True,
    )

    roe: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 6),
        nullable=True,
    )

    operating_cash_flow: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 2),
        nullable=True,
    )

    source: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "stock_id",
            "period_end",
            "period_type",
            "source",
            name="uq_financials_stock_period_source",
        ),
    )
