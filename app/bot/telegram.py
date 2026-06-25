import httpx

from ..otodom import ListingDTO

# Thin wrapper over the Telegram Bot API (sendMessage / sendPhoto / setWebhook),
# using httpx for outbound calls. One client per process, reused across polls.

API_BASE = "https://api.telegram.org"


class TelegramClient:
    """Sends messages/listings to individual subscriber chats."""

    def __init__(self, bot_token: str) -> None:
        self._base = f"{API_BASE}/bot{bot_token}"
        self._client = httpx.AsyncClient(timeout=30)

    async def close(self) -> None:
        """Close the underlying httpx client."""
        await self._client.aclose()

    async def set_webhook(self, url: str, secret: str | None = None) -> None:
        """Register `url` as this bot's webhook (Telegram setWebhook).

        Limits delivery to the message updates the router handles, and passes
        the secret token Telegram will echo back for verification.
        """
        payload: dict = {"url": url, "allowed_updates": ["message", "edited_message"]}
        if secret:
            payload["secret_token"] = secret
        resp = await self._client.post(f"{self._base}/setWebhook", json=payload)
        resp.raise_for_status()
        body = resp.json()
        if not body.get("ok"):
            raise RuntimeError(f"setWebhook failed: {body.get('description', body)}")

    async def send_message(self, chat_id: int, text: str) -> None:
        """Send a plain text message to one chat. STUB."""
        raise NotImplementedError

    async def send_listing(self, chat_id: int, listing: ListingDTO) -> None:
        """Send a formatted listing to one chat.

        STUB: will format `listing` and call sendPhoto when image_url is
        present, else sendMessage.
        """
        raise NotImplementedError

    def format_listing(self, listing: ListingDTO) -> str:
        """Render a listing as a Telegram (HTML/Markdown) message body.

        STUB: returns a placeholder until the message template is finalized.
        """
        return f"{listing.title}\n{listing.url}"
