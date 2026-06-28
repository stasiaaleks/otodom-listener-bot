import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .bot import TelegramClient
from .config import settings
from .poller import Poller
from .storage import Store

log = logging.getLogger(__name__)

# .NET-style IoC container: a single place to wire up all the app's dependencies
# TODO: currently is an experiment. Needs to be reconsidered after testing.
class Container:
    def __init__(self) -> None:
        self.store = Store(settings.database_url)
        self.telegram = TelegramClient(settings.bot_token)
        self.poller = Poller(self.store, self.telegram)
        self.scheduler = AsyncIOScheduler()
        self._add_poll_job()

    async def startup(self) -> None:
        await self.store.init()
        await self.store.migrate()
        self.scheduler.start()

    async def shutdown(self) -> None:
        self.scheduler.shutdown(wait=False)
        await self.telegram.close()
        await self.store.close()
        
    def _add_poll_job(self) -> None:
        self.scheduler.add_job(
            self.poller.poll_once,
            trigger="interval",
            seconds=settings.poll_interval_seconds,
            id="otodom-poll",
            max_instances=1,  # never overlap two polls
            coalesce=True,  # collapse missed runs into one
        )
