import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api import router
from .bot import TelegramClient
from .config import settings
from .poller import create_scheduler
from .storage import Store

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: build long-lived clients and start the poll loop.
    store = Store(settings.database_url)
    telegram = TelegramClient(settings.bot_token)
    # TODO: await store.init() once storage is implemented.
    # TODO: await telegram.set_webhook(<public_url>/telegram/webhook, settings.webhook_secret)
    scheduler = create_scheduler(store, telegram)
    scheduler.start()

    app.state.store = store
    app.state.telegram = telegram
    app.state.scheduler = scheduler

    yield

    # Shutdown: stop the loop and release clients.
    scheduler.shutdown(wait=False)
    # TODO: await telegram.close() and await store.close() once implemented.


app = FastAPI(title="Otodom Telegram Bot", lifespan=lifespan)
app.include_router(router)
