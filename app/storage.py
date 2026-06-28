import asyncpg


class Store:
    """Subscribers + seen-set persistence for the bot."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None

    async def init(self) -> None:
        """Open the connection pool and create the schema if needed."""
        self._pool = await asyncpg.create_pool(self._dsn)
        await self._pool.execute(
            """
            CREATE TABLE IF NOT EXISTS subscribers (
                chat_id       BIGINT PRIMARY KEY,
                subscribed_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            CREATE TABLE IF NOT EXISTS seen (
                id         BIGINT PRIMARY KEY,
                first_seen TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            """
        )

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool is not None:
            await self._pool.close()

    async def add_subscriber(self, chat_id: int) -> None:
        """Record a chat as subscribed (idempotent)."""
        await self._pool.execute(
            "INSERT INTO subscribers (chat_id) VALUES ($1) ON CONFLICT (chat_id) DO NOTHING",
            chat_id,
        )

    async def remove_subscriber(self, chat_id: int) -> None:
        """Drop a chat's subscription (idempotent)."""
        await self._pool.execute("DELETE FROM subscribers WHERE chat_id = $1", chat_id)

    async def list_subscribers(self) -> list[int]:
        """All currently subscribed chat ids."""
        rows = await self._pool.fetch("SELECT chat_id FROM subscribers")
        return [row["chat_id"] for row in rows]

    async def count_subscribers(self) -> int:
        """Number of active subscribers."""
        return await self._pool.fetchval("SELECT count(*) FROM subscribers")

    async def filter_new(self, ids: list[int]) -> list[int]:
        """Return the subset of listing ids not yet recorded."""
        if not ids:
            return []
        rows = await self._pool.fetch(
            "SELECT id FROM seen WHERE id = ANY($1::bigint[])", ids
        )
        seen = {row["id"] for row in rows}
        return [listing_id for listing_id in ids if listing_id not in seen]

    async def mark_seen(self, ids: list[int]) -> None:
        """Record listing ids as sent."""
        if not ids:
            return
        await self._pool.executemany(
            "INSERT INTO seen (id) VALUES ($1) ON CONFLICT (id) DO NOTHING",
            [(listing_id,) for listing_id in ids],
        )

    async def count_seen(self) -> int:
        """Number of listings recorded so far."""
        return await self._pool.fetchval("SELECT count(*) FROM seen")
