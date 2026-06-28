-- Initial schema: subscribers and the seen-set.
-- IF NOT EXISTS keeps this safe to apply to a database that was already
-- bootstrapped by the old Store.init() before migrations were introduced.

CREATE TABLE IF NOT EXISTS subscribers (
    chat_id       BIGINT PRIMARY KEY,
    subscribed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS seen (
    id         BIGINT PRIMARY KEY,
    first_seen TIMESTAMPTZ NOT NULL DEFAULT now()
);
