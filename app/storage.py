


class Store:
    """Subscribers + seen-set persistence for the bot."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool = None  # asyncpg.Pool, created in init()

    async def init(self) -> None:
        """Open the connection pool and create the schema if needed.

        STUB: will asyncpg.create_pool(self._dsn) and create:
          subscribers (chat_id BIGINT PRIMARY KEY, subscribed_at TIMESTAMPTZ DEFAULT now())
          seen        (id BIGINT PRIMARY KEY, first_seen TIMESTAMPTZ DEFAULT now())
        """
        raise NotImplementedError

    async def close(self) -> None:
        """Close the connection pool. STUB."""
        raise NotImplementedError


    async def add_subscriber(self, chat_id: int) -> None:
        """Record a chat as subscribed (idempotent). STUB."""
        raise NotImplementedError

    async def remove_subscriber(self, chat_id: int) -> None:
        """Drop a chat's subscription (idempotent). STUB."""
        raise NotImplementedError

    async def list_subscribers(self) -> list[int]:
        """All currently subscribed chat ids. STUB."""
        raise NotImplementedError

    async def count_subscribers(self) -> int:
        """Number of active subscribers. STUB."""
        raise NotImplementedError


    async def filter_new(self, ids: list[int]) -> list[int]:
        """Return the subset of listing ids not yet recorded. STUB."""
        raise NotImplementedError

    async def mark_seen(self, ids: list[int]) -> None:
        """Record listing ids as sent. STUB."""
        raise NotImplementedError

    async def count_seen(self) -> int:
        """Number of listings recorded so far. STUB."""
        raise NotImplementedError
