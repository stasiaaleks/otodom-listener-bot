import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .bot import TelegramClient
from .config import settings
from .otodom import HTMLPageProvider, ListingParser
from .storage import Store

log = logging.getLogger(__name__)


async def poll_once(store: Store, telegram: TelegramClient) -> None:
    """Run one poll cycle: fetch -> parse -> filter new -> broadcast -> mark seen.

    STUB: wiring is sketched below but left inert so the running app does not
    raise on every scheduled tick. Drop the early return once the pieces below
    are implemented.
    """
    log.info("poll_once: not implemented yet (no-op tick)")
    return

    # --- target shape of a cycle (enable once the stubs above are filled) ---
    html = await HTMLPageProvider().fetch_search_html(settings.search_url)
    listings = ListingParser().parse_next_data(html)
    new_ids = await store.filter_new([listing.id for listing in listings])
    if not new_ids:
        return
    by_id = {listing.id: listing for listing in listings}
    subscribers = await store.list_subscribers()
    for chat_id in subscribers:
        for listing_id in new_ids:
            await telegram.send_listing(chat_id, by_id[listing_id])
    await store.mark_seen(new_ids)


def create_scheduler(store: Store, telegram: TelegramClient) -> AsyncIOScheduler:
    """Build (but do not start) the APScheduler instance that drives polling."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        poll_once,
        trigger="interval",
        seconds=settings.poll_interval_seconds,
        args=[store, telegram],
        id="otodom-poll",
        max_instances=1,  # never overlap two polls
        coalesce=True,  # collapse missed runs into one
    )
    return scheduler
