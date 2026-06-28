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

For inbound commands, expose a public HTTPS URL (front with nginx — see
`deploy/`) and set `PUBLIC_URL`. On startup the app registers the webhook with
Telegram automatically (`PUBLIC_URL` + `/telegram/webhook`). Left unset, the app
runs without inbound webhook (warns and skips registration).

## Docker

```bash
cp .env.sample .env        # fill in secrets
docker compose up -d --build
```

## Deploy (VM)

The bot is deployed at `/opt/otodom-bot` behind nginx, reachable at
`https://otodom-bot.duckdns.org` (DuckDNS A record → the VM).

```bash
# first run: install prerequisites, build, and start everything
sudo /opt/otodom-bot/deploy/deploy.sh --install
# one-time TLS: issue a Let's Encrypt cert and add the TLS vhost via certbot
sudo /opt/otodom-bot/deploy/setup-tls.sh you@example.com
# set PUBLIC_URL=https://otodom-bot.duckdns.org in .env, then redeploy:
sudo /opt/otodom-bot/deploy/deploy.sh
```

`deploy.sh` is idempotent: `git pull` → build → migrate → restart containers →
reload nginx → health-gate on `/health`. Pass `--install` on the first run to
install git/docker. `setup-tls.sh` installs the HTTP reverse-proxy vhost
(`deploy/nginx.conf.sample`, proxying to `127.0.0.1:8000`) and runs
`certbot --nginx`, which obtains the cert and adds the TLS block + HTTP→HTTPS
redirect; renewals run via certbot's timer. Requires inbound 80 and 443 open on
the VM.

## Recon

Run `recon.py` **on the deployment VM** to confirm plain HTTP can reach the
listings JSON and to capture a real listing record:

```bash
pip install curl_cffi beautifulsoup4
python recon.py
```

## Next steps

1. Implement `HTMLPageProvider.fetch_search_html` (curl_cffi, status/challenge checks).
2. Verify nested field names in `ListingParser` against `sample_listing.json`.
3. Implement `storage.Store` (asyncpg: subscribers + seen) and call
   `init()` / `close()` in lifespan.
4. Implement the remaining `TelegramClient` stubs (`send_message`,
   `send_listing`, `format_listing`). _(`set_webhook` / `close` are done.)_
5. Remove the early `return` in `poller.poll_once`.
```
