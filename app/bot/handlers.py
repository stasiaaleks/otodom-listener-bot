import logging

from pydantic import ValidationError

from ..storage import Store
from .router import default_router
from .schemas import TelegramUpdate
from .telegram import TelegramClient

log = logging.getLogger(__name__)


async def handle_update(update: dict, store: Store, telegram: TelegramClient) -> None:
    """Webhook entry point: validate the raw payload, then route it to a command.

    The command strategies call the store / telegram stubs, so a valid command
    raises NotImplementedError until those land.
    """
    try:
        parsed = TelegramUpdate.model_validate(update)
    except ValidationError:
        log.error("ignoring malformed Telegram update: %r", update)
        return
    await default_router.handle_update(parsed, store, telegram)
