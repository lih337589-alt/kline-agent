from redis import Redis


class RedisCache:
    def __init__(
        self,
        url: str,
        default_ttl_seconds: int = 300,
    ) -> None:
        self.client = Redis.from_url(
            url,
            decode_responses=True,
        )

        self.default_ttl_seconds = default_ttl_seconds

    def ping(self) -> bool:
        return bool(self.client.ping())

    def get(
        self,
        key: str,
    ) -> str | None:
        value = self.client.get(key)

        if value is None:
            return None

        return str(value)

    def set(
        self,
        key: str,
        value: str,
        ttl_seconds: int | None = None,
    ) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds

        self.client.set(
            name=key,
            value=value,
            ex=ttl,
        )

    def delete(
        self,
        key: str,
    ) -> None:
        self.client.delete(key)
