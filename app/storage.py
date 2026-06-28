import asyncpg

from .db import apply_migrations
from .queries import queries


class Store:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None

    async def init(self) -> None:
        self._pool = await asyncpg.create_pool(self._dsn)

    @property
    def _db(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("Store not initialized — call init() first")
        return self._pool

    async def migrate(self) -> list[str]:
        async with self._db.acquire() as conn:
            return await apply_migrations(conn)

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()

    async def add_subscriber(self, chat_id: int) -> None:
        await queries.add_subscriber(self._db, chat_id=chat_id)

    async def remove_subscriber(self, chat_id: int) -> None:
        await queries.remove_subscriber(self._db, chat_id=chat_id)

    async def list_subscribers(self) -> list[int]:
        # aiosql's asyncpg multi-row select is an async generator
        return [row["chat_id"] async for row in queries.list_subscribers(self._db)]

    async def count_subscribers(self) -> int:
        return await queries.count_subscribers(self._db)

    async def filter_new(self, ids: list[int]) -> list[int]:
        if not ids:
            return []
        seen = {row["id"] async for row in queries.select_seen(self._db, ids=ids)}
        return [listing_id for listing_id in ids if listing_id not in seen]

    async def mark_seen(self, ids: list[int]) -> None:
        if not ids:
            return
        await queries.mark_seen(self._db, [{"id": listing_id} for listing_id in ids])

    async def count_seen(self) -> int:
        return await queries.count_seen(self._db)
