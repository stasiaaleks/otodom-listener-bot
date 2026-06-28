import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from .api import router
from .api.routes import WEBHOOK_PATH
from .bot import TelegramClient
from .bot.router import CommandRouter, HelpCommand, StartCommand, StopCommand
from .config import settings
from .poller import Poller
from .storage import Store

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # composition root 
    store = Store(settings.database_url)
    telegram = TelegramClient(settings.bot_token)
    poller = Poller(store, telegram)

    help_cmd = HelpCommand()  # doubles as the fallback for unknown commands
    command_router = CommandRouter(
        commands=[StartCommand(), StopCommand(), help_cmd], fallback=help_cmd
    )

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        poller.poll_once,
        trigger="interval",
        seconds=settings.poll_interval_seconds,
        id="otodom-poll",
        max_instances=1,  # never overlap two polls
        coalesce=True,  # collapse missed runs into one
    )

    await store.init()
    await store.migrate()
    scheduler.start()

    if settings.public_url:
        webhook_url = settings.public_url.rstrip("/") + WEBHOOK_PATH
        await telegram.set_webhook(webhook_url, settings.webhook_secret)
        log.info(f"registered Telegram webhook: {webhook_url}")
    else:
        log.warning("PUBLIC_URL not set — skipping Telegram webhook registration")

    app.state.store = store
    app.state.telegram = telegram
    app.state.scheduler = scheduler
    app.state.poller = poller
    app.state.router = command_router

    yield

    scheduler.shutdown(wait=False)
    await telegram.close()
    await store.close()


app = FastAPI(title="Otodom Telegram Bot", lifespan=lifespan)
app.include_router(router)
