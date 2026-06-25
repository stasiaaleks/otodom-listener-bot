import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api import router
from .api.routes import WEBHOOK_PATH
from .bot import TelegramClient
from .config import settings
from .poller import create_scheduler
from .storage import Store

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: build long-lived clients and start the poll loop.
    store = Store(settings.database_url)
    telegram = TelegramClient(settings.bot_token)
    # TODO: await store.init() once storage is implemented.

    if settings.public_url:
        webhook_url = settings.public_url.rstrip("/") + WEBHOOK_PATH
        await telegram.set_webhook(webhook_url, settings.webhook_secret)
        log.info("registered Telegram webhook: %s", webhook_url)
    else:
        log.warning("PUBLIC_URL not set — skipping Telegram webhook registration")

    scheduler = create_scheduler(store, telegram)
    scheduler.start()

    app.state.store = store
    app.state.telegram = telegram
    app.state.scheduler = scheduler

    yield

    # Shutdown: stop the loop and release clients.
    scheduler.shutdown(wait=False)
    await telegram.close()
    # TODO: await store.close() once storage is implemented.


app = FastAPI(title="Otodom Telegram Bot", lifespan=lifespan)
app.include_router(router)
