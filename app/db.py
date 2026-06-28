import logging
from pathlib import Path

import asyncpg
from asyncpg.pool import PoolConnectionProxy

from .queries import queries

log = logging.getLogger(__name__)


Conn = asyncpg.Connection | PoolConnectionProxy

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"

_MIGRATION_LOCK_KEY = 728_274_001


# Applies pending .sql migrations in order, each exactly once, tracked in schema_migrations.
# Each runs in its own transaction (a failure rolls back only the failing one).
# Returns the versions applied this call.
async def apply_migrations(conn: Conn) -> list[str]:
    await queries.lock_migrations(conn, key=_MIGRATION_LOCK_KEY)
    try:
        await queries.create_migrations_table(conn)
        applied = {row["version"] async for row in queries.applied_migrations(conn)}

        files = sorted(MIGRATIONS_DIR.glob("*.sql"), key=lambda p: p.name)
        if not files:
            log.warning(f"no migration files found in {MIGRATIONS_DIR}")

        newly_applied: list[str] = []
        for path in files:
            version = path.name
            if version in applied:
                continue
            # The migration body is dynamic file content, so it's executed
            # directly rather than as a named aiosql query.
            sql = path.read_text(encoding="utf-8")
            async with conn.transaction():
                await conn.execute(sql)
                await queries.record_migration(conn, version=version)
            log.info(f"applied migration {version}")
            newly_applied.append(version)

        if not newly_applied:
            log.info(f"database schema up to date ({len(applied)} migrations)")
        return newly_applied
    finally:
        await queries.unlock_migrations(conn, key=_MIGRATION_LOCK_KEY)
