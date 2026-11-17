from datetime import datetime, timezone

from app.data.providers.base import (
    ProviderRecord,
)
from app.services.text_normalizer import (
    keyword_hits,
    make_title_hash,
    normalize_provider_record,
)


def test_normalize_provider_record() -> None:
    record = ProviderRecord(
        timestamp=datetime(
            2026,
            9,
            10,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        symbol=" aapl ",
        source=" sample ",
        value={
            "title": ("Apple    demand update"),
            "content": ("Demand\n remains   strong."),
            "source_url": ("https://example.test/aapl"),
            "category": "news",
        },
    )

    normalized = normalize_provider_record(record)

    assert normalized.symbol == "AAPL"

    assert normalized.title == "Apple demand update"

    assert normalized.content == "Demand remains strong."

    assert normalized.category == "news"


def test_title_hash_is_stable() -> None:
    first = make_title_hash("Apple   demand update")

    second = make_title_hash(" apple demand update ")

    assert first == second


def test_research_category_is_supported() -> None:
    record = ProviderRecord(
        timestamp=datetime.now(timezone.utc),
        symbol="MSFT",
        source="sample",
        value={
            "title": "Microsoft research",
            "content": "Sample text",
            "category": "research",
        },
    )

    normalized = normalize_provider_record(record)

    assert normalized.category == "research"


def test_keyword_hits_are_filter_only() -> None:
    record = ProviderRecord(
        timestamp=datetime.now(timezone.utc),
        symbol="AAPL",
        source="sample",
        value={
            "title": "Apple demand update",
            "content": ("Revenue demand remains strong."),
            "category": "news",
        },
    )

    normalized = normalize_provider_record(record)

    hits = keyword_hits(
        normalized,
        [
            "revenue",
            "risk",
            "demand",
        ],
    )

    assert hits == [
        "revenue",
        "demand",
    ]
