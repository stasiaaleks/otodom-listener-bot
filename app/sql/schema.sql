-- name: lock_migrations(key)$
SELECT pg_advisory_lock(:key);

-- name: unlock_migrations(key)$
SELECT pg_advisory_unlock(:key);

-- name: create_migrations_table()#
CREATE TABLE IF NOT EXISTS schema_migrations (
    version    TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- name: applied_migrations()
SELECT version FROM schema_migrations;

-- name: record_migration(version)!
INSERT INTO schema_migrations (version) VALUES (:version);
