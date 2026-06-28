-- name: select_seen(ids)
-- Which of the given ids are already recorded. No ::bigint[] cast: asyncpg
-- infers the array type from the bigint `id` column in `= ANY(:ids)`.
SELECT id FROM seen WHERE id = ANY(:ids);

-- name: mark_seen(id)*!
INSERT INTO seen (id)
VALUES (:id)
ON CONFLICT (id) DO NOTHING;

-- name: count_seen()$
SELECT count(*) FROM seen;
