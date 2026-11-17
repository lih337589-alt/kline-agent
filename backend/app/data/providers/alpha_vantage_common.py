import time
from typing import Any

import httpx

from app.data.providers.base import ProviderError


class AlphaVantageClient:
    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(
        self,
        api_key: str,
        timeout_seconds: float = 20.0,
        min_interval_seconds: float = 1.2,
    ) -> None:
        api_key = api_key.strip()

        if not api_key:
            raise ValueError("Alpha Vantage API key is empty.")

        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.min_interval_seconds = min_interval_seconds

        self._last_request_started_at: float | None = None

    def _wait_for_rate_limit(self) -> None:
        if self._last_request_started_at is None:
            return

        elapsed = time.monotonic() - self._last_request_started_at

        remaining = self.min_interval_seconds - elapsed

        if remaining > 0:
            time.sleep(remaining)

    def get(
        self,
        *,
        function: str,
        symbol: str,
        extra_params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        params = {
            "function": function,
            "symbol": symbol,
            "apikey": self.api_key,
        }

        if extra_params:
            params.update(extra_params)

        self._wait_for_rate_limit()

        self._last_request_started_at = time.monotonic()

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(
                    self.BASE_URL,
                    params=params,
                )

                response.raise_for_status()
                data = response.json()

        except (
            httpx.HTTPError,
            ValueError,
        ) as exc:
            raise ProviderError(
                f"Alpha Vantage request failed: function={function} symbol={symbol}"
            ) from exc

        if not isinstance(data, dict):
            raise ProviderError("Alpha Vantage returned an unexpected response format.")

        for error_key in (
            "Error Message",
            "Note",
            "Information",
        ):
            message = data.get(error_key)

            if message:
                raise ProviderError(f"Alpha Vantage error: {message}")

        return data
