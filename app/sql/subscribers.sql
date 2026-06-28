-- name: add_subscriber(chat_id)!
INSERT INTO subscribers (chat_id)
VALUES (:chat_id)
ON CONFLICT (chat_id) DO NOTHING;

-- name: remove_subscriber(chat_id)!
DELETE FROM subscribers WHERE chat_id = :chat_id;

-- name: list_subscribers()
SELECT chat_id FROM subscribers;

-- name: count_subscribers()$
SELECT count(*) FROM subscribers;
