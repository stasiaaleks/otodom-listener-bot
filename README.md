# Otodom Telegram Bot

A Telegram bot that polls an Otodom rental search page and pushes each new
listing to its subscribers. Users `/start` the bot to subscribe and `/stop` to
unsubscribe; inbound commands arrive via a Telegram webhook.

> **Status: scaffold.** The structure compiles and runs, but the fetch / parse-
> wiring / storage / Telegram pieces are stubs (`NotImplementedError`). The poll
> loop is registered and ticks on schedule as a logged no-op until they land.

## How it works

- **Inbound** — Telegram delivers updates to `POST /telegram/webhook`; `bot.py`
  dispatches `/start` / `/stop` to add/remove the subscriber.
- **Outbound** — `poller.py` polls Otodom on an interval, diffs against the
  seen-set, and sends each new listing to every subscriber.

## Layout

```
app/
  main.py            FastAPI app + lifespan (starts/stops the poll scheduler)
  config.py          Settings loaded from environment / .env
  storage.py         Postgres subscribers + seen-set, via asyncpg      [stub]
  poller.py          One poll cycle (broadcast to subscribers) + scheduler
  api/
    routes.py        /health, /status, and the Telegram webhook
  bot/
    handlers.py      Inbound command dispatch (/start, /stop)
    telegram.py      Telegram Bot API client + message formatting      [stub]
  otodom/
    fetcher.py       Fetch search HTML (curl_cffi, Chrome impersonation)  [stub]
    parser.py        Extract listings from embedded __NEXT_DATA__ JSON
    models.py        Pydantic models (Listing, Money)
recon.py             Standalone script to probe Otodom and dump a sample listing
deploy/              deploy.sh + nginx reverse-proxy sample
```

## Local run

```bash
pip install -e ".[dev]"
cp .env.sample .env        # fill in BOT_TOKEN (WEBHOOK_SECRET optional)
uvicorn app.main:app --reload
curl -s http://127.0.0.1:8000/health
```

The webhook needs a public HTTPS URL (front with nginx — see `deploy/`), then
register it once: `setWebhook` to `https://<host>/telegram/webhook`.

## Docker

```bash
cp .env.sample .env        # fill in secrets
docker compose up -d --build
```

## Recon

Run `recon.py` **on the deployment VM** to confirm plain HTTP can reach the
listings JSON and to capture a real listing record:

```bash
pip install curl_cffi beautifulsoup4
python recon.py
```

## Next steps

1. Implement `fetcher.fetch_search_html` (curl_cffi, status/challenge checks).
2. Verify nested field names in `parser.py` against `sample_listing.json`.
3. Implement `storage.Store` (asyncpg: subscribers + seen) and call
   `init()` / `close()` in lifespan.
4. Implement `telegram.TelegramClient` (`send_message`, `send_listing`,
   `set_webhook`) + `format_listing`.
5. Remove the early `return` in `poller.poll_once`.
```
