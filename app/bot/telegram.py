import html

import httpx

from ..otodom import FinancialDTO, ListingDTO

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

    async def send_message(
        self, chat_id: int, text: str, parse_mode: str | None = None
    ) -> None:
        """Send a text message to one chat (Telegram sendMessage)."""
        payload: dict = {"chat_id": chat_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        resp = await self._client.post(f"{self._base}/sendMessage", json=payload)
        resp.raise_for_status()
        body = resp.json()
        if not body.get("ok"):
            raise RuntimeError(f"sendMessage failed: {body.get('description', body)}")

    async def send_photo(
        self, chat_id: int, photo: str, caption: str, parse_mode: str | None = "HTML"
    ) -> None:
        """Send a photo with a caption to one chat (Telegram sendPhoto)."""
        payload: dict = {"chat_id": chat_id, "photo": photo, "caption": caption}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        resp = await self._client.post(f"{self._base}/sendPhoto", json=payload)
        resp.raise_for_status()
        body = resp.json()
        if not body.get("ok"):
            raise RuntimeError(f"sendPhoto failed: {body.get('description', body)}")

    async def send_listing(self, chat_id: int, listing: ListingDTO) -> None:
        """Send a formatted listing to one chat.

        Uses sendPhoto with an HTML caption when the listing has an image, and
        falls back to a plain HTML text message otherwise.
        """
        caption = self.format_listing(listing)
        if listing.image_url:
            await self.send_photo(chat_id, listing.image_url, caption)
        else:
            await self.send_message(chat_id, caption, parse_mode="HTML")

    def format_listing(self, listing: ListingDTO) -> str:
        """Render a listing as a Telegram HTML message body.

        Only fields that are present are included, so the template degrades
        gracefully for sparse listings. All interpolated text is HTML-escaped
        because the message is sent with parse_mode=HTML.
        """
        title = html.escape(listing.title or "Listing")
        lines = [f'<a href="{html.escape(listing.url, quote=True)}"><b>{title}</b></a>']

        price = self._format_money(listing.total) or self._format_money(listing.rent)
        if price:
            lines.append(f"💰 {price}")

        details: list[str] = []
        if listing.area_m2:
            details.append(f"{listing.area_m2:g} m²")
        if listing.rooms:
            details.append(f"{listing.rooms} rooms")
        if details:
            lines.append("📐 " + " · ".join(details))

        if listing.location:
            lines.append("📍 " + html.escape(listing.location))
        if listing.is_private_owner:
            lines.append("🔑 private owner")

        return "\n".join(lines)

    @staticmethod
    def _format_money(money: FinancialDTO | None) -> str | None:
        """Render a price as e.g. '3500 PLN', or None when unavailable."""
        if money is None or money.value is None:
            return None
        amount = f"{money.value:,.0f}".replace(",", " ")
        return f"{amount} {money.currency}".strip() if money.currency else amount
