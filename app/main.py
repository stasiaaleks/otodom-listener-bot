import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api import router
from .api.routes import WEBHOOK_PATH
from .config import settings
from .ioc_container import Container

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    container = Container()
    await container.startup()

    if settings.public_url:
        webhook_url = settings.public_url.rstrip("/") + WEBHOOK_PATH
        await container.telegram.set_webhook(webhook_url, settings.webhook_secret)
        log.info(f"registered Telegram webhook: {webhook_url}")
    else:
        log.warning("PUBLIC_URL not set — skipping Telegram webhook registration")

    app.state.store = container.store
    app.state.telegram = container.telegram
    app.state.scheduler = container.scheduler
    app.state.poller = container.poller

    yield

    await container.shutdown()


app = FastAPI(title="Otodom Telegram Bot", lifespan=lifespan)
app.include_router(router)
