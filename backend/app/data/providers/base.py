from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ProviderError(RuntimeError):
    pass


class ProviderRecord(BaseModel):
    timestamp: datetime
    symbol: str
    source: str
    value: dict[str, Any] = Field(default_factory=dict)


class MarketDataProvider(ABC):
    @abstractmethod
    def get_market_data(
        self,
        symbol: str,
    ) -> list[ProviderRecord]:
        pass


class FinancialDataProvider(ABC):
    @abstractmethod
    def get_financial_data(
        self,
        symbol: str,
    ) -> list[ProviderRecord]:
        pass


class NewsProvider(ABC):
    @abstractmethod
    def get_news(
        self,
        symbol: str,
    ) -> list[ProviderRecord]:
        pass
