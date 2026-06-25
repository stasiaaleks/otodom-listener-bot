from __future__ import annotations

import logging

from ..storage import Store
from .telegram import TelegramClient

log = logging.getLogger(__name__)

WELCOME = "You're subscribed — I'll send new Otodom listings as they appear. Send /stop to unsubscribe."
GOODBYE = "You're unsubscribed. Send /start any time to resume."
HELP = "Send /start to subscribe to new listings, or /stop to unsubscribe."


async def handle_update(update: dict, store: Store, telegram: TelegramClient) -> None:
    """Process one inbound Telegram update (delivered via the webhook).

    Command dispatch is wired; the store / telegram calls it makes are still
    stubs, so this raises NotImplementedError until those land.
    """
    message = update.get("message") or update.get("edited_message") or {}
    chat_id = (message.get("chat") or {}).get("id")
    text = (message.get("text") or "").strip()
    if chat_id is None:
        return  # non-message update (callback query, etc.) — ignore for now

    command = text.split(maxsplit=1)[0].lower()
    if command == "/start":
        await store.add_subscriber(chat_id)
        await telegram.send_message(chat_id, WELCOME)
    elif command == "/stop":
        await store.remove_subscriber(chat_id)
        await telegram.send_message(chat_id, GOODBYE)
    else:
        await telegram.send_message(chat_id, HELP)
