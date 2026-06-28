import logging

from pydantic import ValidationError

from ..storage import Store
from .router import CommandRouter
from .schemas import TelegramUpdate
from .telegram import TelegramClient

log = logging.getLogger(__name__)


async def handle_update(
    update: dict, router: CommandRouter, store: Store, telegram: TelegramClient
) -> None:
    """Webhook entry point: validate the raw payload, then route it to a command."""
    try:
        parsed = TelegramUpdate.model_validate(update)
    except ValidationError:
        log.error(f"ignoring malformed Telegram update: {update!r}")
        return
    await router.handle_update(parsed, store, telegram)
