import logging
from datetime import datetime, timezone

from .bot import TelegramClient
from .config import settings
from .otodom import HTMLPageProvider, ListingParser
from .storage import Store

log = logging.getLogger(__name__)


class Poller:
    def __init__(self, store: Store, telegram: TelegramClient) -> None:
        self._store = store
        self._telegram = telegram
        self._html_provider = HTMLPageProvider()
        self._parser = ListingParser()
        self.last_poll_at: datetime | None = None  # UTC start of the most recent cycle

    async def poll_once(self) -> None:
        """Run one poll cycle: fetch -> parse -> filter new -> broadcast -> mark seen."""
        self.last_poll_at = datetime.now(timezone.utc)
        try:
            html = await self._html_provider.fetch_search_html(settings.build_search_url())
            listings = self._parser.parse_next_data(html)
        except Exception:
            log.exception("poll_once: fetch/parse failed")
            return

        ids = [listing.id for listing in listings]
        new_ids = await self._store.filter_new(ids)
        if not new_ids:
            log.info(f"poll_once: {len(ids)} listings, none new")
            return

        # initial run for a new subscriber
        if await self._store.count_seen() == 0:
            await self._store.mark_seen(ids)
            log.info(f"poll_once: seeded seen-set with {len(ids)} listings (no broadcast)")
            return

        by_id = {listing.id: listing for listing in listings}
        subscribers = await self._store.list_subscribers()
        log.info(f"poll_once: broadcasting {len(new_ids)} new listings to {len(subscribers)} subscribers")

        for listing_id in new_ids:
            for chat_id in subscribers:
                try:
                    await self._telegram.send_listing(chat_id, by_id[listing_id])
                except Exception:
                    log.exception(f"poll_once: send_listing failed chat={chat_id} listing={listing_id}")

        await self._store.mark_seen(new_ids)
