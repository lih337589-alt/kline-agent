import hashlib
import re
from datetime import timezone
from typing import cast

from app.data.providers.base import ProviderRecord
from app.schemas.text import NormalizedText, TextCategory

_ALLOWED_CATEGORIES = {
    "announcement",
    "news",
    "research",
}

_WHITESPACE_PATTERN = re.compile(r"\s+")


class TextNormalizationError(ValueError):
    pass


def normalize_whitespace(value: str) -> str:
    return _WHITESPACE_PATTERN.sub(
        " ",
        value,
    ).strip()


def make_title_hash(title: str) -> str:
    normalized_title = normalize_whitespace(title).casefold()

    return hashlib.sha256(normalized_title.encode("utf-8")).hexdigest()


def normalize_provider_record(
    record: ProviderRecord,
) -> NormalizedText:
    symbol = record.symbol.strip().upper()

    if not symbol:
        raise TextNormalizationError("symbol cannot be empty")

    raw_title = record.value.get("title")

    if raw_title is None:
        raise TextNormalizationError("title is required")

    title = normalize_whitespace(str(raw_title))

    if not title:
        raise TextNormalizationError("title cannot be empty")

    raw_content = record.value.get(
        "content",
        "",
    )

    content = normalize_whitespace(str(raw_content or ""))

    source = normalize_whitespace(record.source)

    if not source:
        raise TextNormalizationError("source cannot be empty")

    raw_source_url = record.value.get("source_url")

    source_url = None

    if raw_source_url:
        cleaned_url = str(raw_source_url).strip()

        if cleaned_url:
            source_url = cleaned_url

    raw_category = record.value.get(
        "category",
        "news",
    )

    category = str(raw_category).strip().lower()

    if category not in _ALLOWED_CATEGORIES:
        raise TextNormalizationError(f"unsupported category: {category}")

    published_at = record.timestamp

    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    else:
        published_at = published_at.astimezone(timezone.utc)

    return NormalizedText(
        symbol=symbol,
        title=title,
        content=content,
        source=source,
        source_url=source_url,
        published_at=published_at,
        category=cast(
            TextCategory,
            category,
        ),
        title_hash=make_title_hash(title),
    )


def keyword_hits(
    text: NormalizedText,
    keywords: list[str],
) -> list[str]:
    haystack = (f"{text.title} {text.content}").casefold()

    hits: list[str] = []

    for keyword in keywords:
        normalized_keyword = keyword.strip().casefold()

        if normalized_keyword and normalized_keyword in haystack:
            hits.append(keyword)

    return hits
