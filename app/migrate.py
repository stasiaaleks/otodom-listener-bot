# Standalone migration entrypoint: `python -m app.migrate`.
# Used by deploy.sh as an explicit, fail-loud gate before the app is (re)started.
# The app also migrates on startup, but running here first means a bad migration
# aborts the deploy instead of crash-looping the container.

import asyncio
import logging

import asyncpg

from .config import settings
from .db import apply_migrations

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


async def _main() -> None:
    conn = await asyncpg.connect(settings.database_url)
    try:
        applied = await apply_migrations(conn)
    finally:
        await conn.close()
    log.info(f"applied {len(applied)} migration(s): {applied or 'none, already current'}")


if __name__ == "__main__":
    asyncio.run(_main())
