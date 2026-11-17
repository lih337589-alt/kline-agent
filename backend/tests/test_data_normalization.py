from pathlib import Path

from app.data.providers.mock import MockProvider

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_market_data_normalization() -> None:
    provider = MockProvider(FIXTURE_DIR)

    records = provider.get_market_data("aapl")

    assert len(records) == 1

    record = records[0]

    assert record.symbol == "AAPL"
    assert record.source == "mock_csv"
    assert record.timestamp.tzinfo is not None
    assert record.value["close"] == 101.0
    assert record.value["volume"] == 1000000


def test_financial_data_normalization() -> None:
    provider = MockProvider(FIXTURE_DIR)

    records = provider.get_financial_data("AAPL")

    assert len(records) == 1

    record = records[0]

    assert record.symbol == "AAPL"
    assert record.source == "mock_csv"
    assert record.timestamp.tzinfo is not None
    assert record.value["period_type"] == "annual"
    assert record.value["eps"] == 5.0


def test_news_data_normalization() -> None:
    provider = MockProvider(FIXTURE_DIR)

    records = provider.get_news("AAPL")

    assert len(records) == 1

    record = records[0]

    assert record.symbol == "AAPL"
    assert record.source == "mock_csv"
    assert record.timestamp.tzinfo is not None
    assert record.value["title"] == "Mock AAPL news"


def test_unknown_symbol_returns_empty_list() -> None:
    provider = MockProvider(FIXTURE_DIR)

    records = provider.get_market_data("ZZZZ")

    assert records == []
