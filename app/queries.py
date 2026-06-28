from pathlib import Path
from typing import Any

import aiosql

# All .sql files under ./sql, loaded once and bound to the asyncpg driver.
# Each `-- name: foo` block becomes an async method queries.foo(conn, ...).
# Typed Any because aiosql builds those methods dynamically at load time.
SQL_DIR = Path(__file__).resolve().parent / "sql"

queries: Any = aiosql.from_path(SQL_DIR, "asyncpg")
