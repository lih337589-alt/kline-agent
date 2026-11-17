from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

TextCategory = Literal[
    "announcement",
    "news",
    "research",
]


class NormalizedText(BaseModel):
    model_config = ConfigDict(frozen=True)

    symbol: str
    title: str
    content: str
    source: str
    source_url: str | None
    published_at: datetime
    category: TextCategory
    title_hash: str


class TextEvidence(BaseModel):
    symbol: str
    category: TextCategory
    title: str
    content: str
    source: str
    source_url: str | None
    published_at: datetime
