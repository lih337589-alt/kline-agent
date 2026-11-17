import logging
from datetime import datetime, time, timezone
from decimal import Decimal
from typing import Protocol

from pydantic import ValidationError
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.limits import (
    CONTEXT_TEXT_CHAR_LIMIT,
    CONTEXT_TEXT_FETCH_LIMIT,
    CONTEXT_TEXT_ITEM_CHAR_LIMIT,
    CONTEXT_TEXT_ITEM_LIMIT,
)
from app.models.announcement import Announcement
from app.models.financial import Financial
from app.models.news import News
from app.models.price import Price
from app.models.stock import Stock
from app.schemas.context import (
    AnalysisContext,
    ContextTextEvidence,
    FinancialEvidence,
    MarketSnapshot,
    SourceReference,
)

logger = logging.getLogger(__name__)


CONTEXT_TTL_SECONDS = 300

PRICE_LIMIT = 30

FINANCIAL_LIMIT = 4


class StringCache(Protocol):
    def get(
        self,
        key: str,
    ) -> str | None:
        pass

    def set(
        self,
        key: str,
        value: str,
        ttl_seconds: int | None = None,
    ) -> None:
        pass


class ContextBuilder:
    def __init__(
        self,
        cache: StringCache | None = None,
    ) -> None:
        self.cache = cache
        self.last_cache_hit = False

    def build(
        self,
        db: Session,
        symbol: str,
        *,
        use_cache: bool = True,
    ) -> AnalysisContext:
        normalized_symbol = symbol.strip().upper()

        if not normalized_symbol:
            raise LookupError("Stock symbol is required")

        cache_key = self._cache_key(normalized_symbol)

        self.last_cache_hit = False

        if self.cache is not None and use_cache:
            cached = self._read_cache(cache_key)

            if cached is not None:
                self.last_cache_hit = True
                return cached

        stock = db.scalar(select(Stock).where(Stock.symbol == normalized_symbol))

        if stock is None:
            raise LookupError(f"Stock not found: {normalized_symbol}")

        context = self._build_context(
            db,
            stock,
        )

        if self.cache is not None and use_cache:
            self._write_cache(
                cache_key,
                context,
            )

        return context

    @staticmethod
    def _cache_key(
        symbol: str,
    ) -> str:
        return f"kline:analysis_context:{symbol}:v1"

    def _read_cache(
        self,
        key: str,
    ) -> AnalysisContext | None:
        if self.cache is None:
            return None

        try:
            raw = self.cache.get(key)

        except RedisError as exc:
            logger.warning(
                "Redis cache read failed: %s",
                exc,
            )
            return None

        if raw is None:
            return None

        try:
            return AnalysisContext.model_validate_json(raw)

        except ValidationError as exc:
            logger.warning(
                "Cached AnalysisContext validation failed: %s",
                exc,
            )

            return None

    def _write_cache(
        self,
        key: str,
        context: AnalysisContext,
    ) -> None:
        if self.cache is None:
            return

        try:
            self.cache.set(
                key,
                context.model_dump_json(),
                ttl_seconds=(CONTEXT_TTL_SECONDS),
            )

        except RedisError as exc:
            logger.warning(
                "Redis cache write failed: %s",
                exc,
            )

    def _build_context(
        self,
        db: Session,
        stock: Stock,
    ) -> AnalysisContext:
        prices = self._load_prices(
            db,
            stock.id,
        )

        financials = self._load_financials(
            db,
            stock.id,
        )

        texts = self._load_texts(
            db,
            stock.id,
        )

        market = self._build_market_snapshot(prices)

        financial_evidence = [self._build_financial(item) for item in financials]

        return AnalysisContext(
            symbol=stock.symbol,
            company_name=stock.name,
            built_at=datetime.now(timezone.utc),
            market=market,
            financials=(financial_evidence),
            texts=texts,
        )

    @staticmethod
    def _load_prices(
        db: Session,
        stock_id: int,
    ) -> list[Price]:
        statement = (
            select(Price)
            .where(Price.stock_id == stock_id)
            .order_by(Price.timestamp.desc())
            .limit(PRICE_LIMIT)
        )

        return list(db.scalars(statement).all())

    @staticmethod
    def _load_financials(
        db: Session,
        stock_id: int,
    ) -> list[Financial]:
        statement = (
            select(Financial)
            .where(Financial.stock_id == stock_id)
            .order_by(Financial.period_end.desc())
            .limit(FINANCIAL_LIMIT)
        )

        return list(db.scalars(statement).all())

    @staticmethod
    def _load_texts(
        db: Session,
        stock_id: int,
    ) -> list[ContextTextEvidence]:
        announcement_statement = (
            select(Announcement)
            .where(Announcement.stock_id == stock_id)
            .order_by(Announcement.published_at.desc())
            .limit(CONTEXT_TEXT_FETCH_LIMIT)
        )

        news_statement = (
            select(News)
            .where(News.stock_id == stock_id)
            .order_by(News.published_at.desc())
            .limit(CONTEXT_TEXT_FETCH_LIMIT)
        )

        announcements = list(db.scalars(announcement_statement).all())

        news_items = list(db.scalars(news_statement).all())

        combined: list[
            tuple[
                str,
                Announcement | News,
                datetime,
            ]
        ] = []

        for item in announcements:
            evidence_time = item.published_at or item.created_at

            if evidence_time is None:
                continue

            combined.append(
                (
                    "announcement",
                    item,
                    _ensure_utc(evidence_time),
                )
            )

        for item in news_items:
            evidence_time = item.published_at or item.created_at

            if evidence_time is None:
                continue

            combined.append(
                (
                    "news",
                    item,
                    _ensure_utc(evidence_time),
                )
            )

        combined.sort(
            key=lambda item: item[2],
            reverse=True,
        )

        evidence: list[ContextTextEvidence] = []

        total_chars = 0

        for (
            category,
            row,
            evidence_time,
        ) in combined:
            if len(evidence) >= CONTEXT_TEXT_ITEM_LIMIT:
                break

            title = _clean_text(row.title or "")

            content = _clean_text(row.content or "")

            content = content[:CONTEXT_TEXT_ITEM_CHAR_LIMIT]

            item_chars = len(title) + len(content)

            if total_chars + item_chars > CONTEXT_TEXT_CHAR_LIMIT:
                remaining = CONTEXT_TEXT_CHAR_LIMIT - total_chars - len(title)

                if remaining <= 0:
                    break

                content = content[:remaining]

                item_chars = len(title) + len(content)

            source_id = f"{category}:{row.id}"

            evidence.append(
                ContextTextEvidence(
                    category=category,
                    title=title,
                    content=content,
                    source_ref=(
                        SourceReference(
                            source_id=(source_id),
                            source=(row.source),
                            source_url=(row.source_url),
                            time=(evidence_time),
                        )
                    ),
                )
            )

            total_chars += item_chars

            if total_chars >= CONTEXT_TEXT_CHAR_LIMIT:
                break

        return evidence

    @staticmethod
    def _build_market_snapshot(
        prices: list[Price],
    ) -> MarketSnapshot:
        if not prices:
            return MarketSnapshot()

        latest = prices[0]

        latest_close = _to_float(latest.close)

        previous_close = None

        daily_return_pct = None

        if len(prices) >= 2:
            previous_close = _to_float(prices[1].close)

            daily_return_pct = _percent_change(
                latest_close,
                previous_close,
            )

        five_day_return_pct = None

        if len(prices) >= 6:
            five_day_close = _to_float(prices[5].close)

            five_day_return_pct = _percent_change(
                latest_close,
                five_day_close,
            )

        volumes = [float(item.volume) for item in prices[:5] if item.volume is not None]

        average_volume_5d = None

        if volumes:
            average_volume_5d = sum(volumes) / len(volumes)

        source_ref = SourceReference(
            source_id=(f"price:{latest.id}"),
            source=latest.source,
            source_url=None,
            time=_ensure_utc(latest.timestamp),
        )

        return MarketSnapshot(
            latest_close=latest_close,
            previous_close=(previous_close),
            daily_return_pct=(daily_return_pct),
            five_day_return_pct=(five_day_return_pct),
            average_volume_5d=(average_volume_5d),
            as_of=_ensure_utc(latest.timestamp),
            price_points_used=len(prices),
            source_ref=source_ref,
        )

    @staticmethod
    def _build_financial(
        financial: Financial,
    ) -> FinancialEvidence:
        period_time = datetime.combine(
            financial.period_end,
            time.min,
            tzinfo=timezone.utc,
        )

        return FinancialEvidence(
            period_end=(financial.period_end),
            period_type=(financial.period_type),
            revenue=_to_float(financial.revenue),
            net_income=_to_float(financial.net_income),
            eps=_to_float(financial.eps),
            roe=_to_float(financial.roe),
            operating_cash_flow=(_to_float(financial.operating_cash_flow)),
            source_ref=(
                SourceReference(
                    source_id=(f"financial:{financial.id}"),
                    source=(financial.source),
                    source_url=None,
                    time=period_time,
                )
            ),
        )


def _to_float(
    value: Decimal | float | None,
) -> float | None:
    if value is None:
        return None

    return float(value)


def _percent_change(
    current: float | None,
    previous: float | None,
) -> float | None:
    if current is None or previous is None or previous == 0:
        return None

    return round(
        (current - previous) / previous * 100,
        4,
    )


def _ensure_utc(
    value: datetime,
) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def _clean_text(
    value: str,
) -> str:
    return " ".join(value.split())
