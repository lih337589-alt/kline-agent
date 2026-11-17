from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Announcement,
    News,
    Stock,
)
from app.schemas.text import (
    TextEvidence,
)


def get_recent_text_evidence(
    db: Session,
    stock: Stock,
    limit: int = 10,
) -> list[TextEvidence]:
    announcement_statement = (
        select(Announcement)
        .where(Announcement.stock_id == stock.id)
        .order_by(Announcement.published_at.desc())
        .limit(limit)
    )

    news_statement = (
        select(News)
        .where(News.stock_id == stock.id)
        .order_by(News.published_at.desc())
        .limit(limit)
    )

    announcements = list(db.scalars(announcement_statement))

    news_items = list(db.scalars(news_statement))

    evidence: list[TextEvidence] = []

    for row in announcements:
        evidence.append(
            TextEvidence(
                symbol=stock.symbol,
                category="announcement",
                title=row.title,
                content=row.content or "",
                source=row.source,
                source_url=row.source_url,
                published_at=(row.published_at),
            )
        )

    for row in news_items:
        evidence.append(
            TextEvidence(
                symbol=stock.symbol,
                category="news",
                title=row.title,
                content=row.content or "",
                source=row.source,
                source_url=row.source_url,
                published_at=(row.published_at),
            )
        )

    evidence.sort(
        key=lambda item: item.published_at,
        reverse=True,
    )

    return evidence[:limit]
