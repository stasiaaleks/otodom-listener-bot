from __future__ import annotations

from ..otodom import ListingDTO

# Thin wrapper over the Telegram Bot API (sendMessage / sendPhoto / setWebhook),
# using httpx for outbound calls. One client per process, reused across polls.

API_BASE = "https://api.telegram.org"



class TelegramClient:
    """Sends messages/listings to individual subscriber chats."""

    def __init__(self, bot_token: str) -> None:
        self._bot_token = bot_token

    async def close(self) -> None:
        """Close the underlying httpx client. STUB."""
        raise NotImplementedError

    async def send_message(self, chat_id: int, text: str) -> None:
        """Send a plain text message to one chat. STUB."""
        raise NotImplementedError

    async def send_listing(self, chat_id: int, listing: ListingDTO) -> None:
        """Send a formatted listing to one chat.

        STUB: will format `listing` and call sendPhoto when image_url is
        present, else sendMessage.
        """
        raise NotImplementedError

    async def set_webhook(self, url: str, secret: str | None = None) -> None:
        """Register the webhook URL with Telegram (setWebhook). STUB."""
        raise NotImplementedError


    def format_listing(self, listing: ListingDTO) -> str:
        """Render a listing as a Telegram (HTML/Markdown) message body.

        STUB: returns a placeholder until the message template is finalized.
        """
        return f"{listing.title}\n{listing.url}"
