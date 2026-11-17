from app.data.providers.news_sample import (
    SampleNewsProvider,
)


def test_sample_news_provider_reads_aapl() -> None:
    provider = SampleNewsProvider("tests/fixtures/day9_texts.csv")

    records = provider.get_news("AAPL")

    assert len(records) == 4

    assert all(record.symbol == "AAPL" for record in records)

    assert records[0].timestamp.tzinfo


def test_sample_news_provider_filters_symbol() -> None:
    provider = SampleNewsProvider("tests/fixtures/day9_texts.csv")

    records = provider.get_news("MSFT")

    assert len(records) == 1

    assert records[0].symbol == "MSFT"

    assert records[0].value["category"] == "research"
