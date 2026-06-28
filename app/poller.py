import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .bot import TelegramClient
from .config import settings
from .otodom import HTMLPageProvider, ListingParser
from .storage import Store

log = logging.getLogger(__name__)


async def poll_once(store: Store, telegram: TelegramClient) -> None:
    """Run one poll cycle: fetch -> parse -> filter new -> broadcast -> mark seen.

    Any failure (fetch block/challenge, parse error, etc.) is logged rather than
    raised, so a single bad tick never tears down the scheduled job.
    """
    try:
        html = await HTMLPageProvider().fetch_search_html(settings.search_url)
        listings = ListingParser().parse_next_data(html)
    except Exception:
        log.exception("poll_once: fetch/parse failed")
        return

    ids = [listing.id for listing in listings]
    new_ids = await store.filter_new(ids)
    if not new_ids:
        log.info("poll_once: %d listings, none new", len(ids))
        return

    # Cold start: an empty seen-set means we've never polled. Seed it silently
    # so subscribers only receive listings that appear *after* they subscribe,
    # instead of a flood of every currently-listed apartment.
    if await store.count_seen() == 0:
        await store.mark_seen(ids)
        log.info("poll_once: seeded seen-set with %d listings (no broadcast)", len(ids))
        return

    by_id = {listing.id: listing for listing in listings}
    subscribers = await store.list_subscribers()
    log.info("poll_once: broadcasting %d new listings to %d subscribers", len(new_ids), len(subscribers))
    for listing_id in new_ids:
        for chat_id in subscribers:
            try:
                await telegram.send_listing(chat_id, by_id[listing_id])
            except Exception:
                # An individual failed send (blocked bot, deleted chat) must not
                # abort the cycle or prevent marking the rest as seen.
                log.exception("poll_once: send_listing failed chat=%s listing=%s", chat_id, listing_id)

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
