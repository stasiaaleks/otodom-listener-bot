from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from ..config import settings
from ..storage import Store
from .schemas import TelegramUpdate
from .telegram import TelegramClient

WELCOME = "You're subscribed — I'll send new Otodom listings as they appear. Send /stop to unsubscribe."
GOODBYE = "You're unsubscribed. Send /start any time to resume."


def _format_interval(seconds: int) -> str:
    # 180 -> "3 minutes", 90 -> "90 seconds"
    if seconds >= 60 and seconds % 60 == 0:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    return f"{seconds} seconds"


def help_text() -> str:
    return (
        "🏠 <b>Otodom Listings Bot</b>\n"
        "I watch an Otodom search and forward new listings here as soon as "
        f"they're posted (checked every {_format_interval(settings.poll_interval_seconds)}).\n\n"
        "<b>Commands</b>\n"
        "/start — subscribe to new listings\n"
        "/stop — stop receiving listings\n"
        "/help — show this message\n\n"
        "Each listing shows its price, size, room count, location and a direct "
        "link. You'll only receive listings posted <i>after</i> you subscribe — "
        "no backlog flood on /start."
    )


@dataclass(slots=True)
class CommandContext:
    """Everything a command strategy needs to act on one inbound message."""

    chat_id: int
    args: str  
    store: Store
    telegram: TelegramClient


class ICommand(Protocol):
    """A command strategy, selected by its `keyword` (e.g. "/start")."""

    keyword: str

    async def execute(self, cmd: CommandContext) -> None: ...


class StartCommand(ICommand):
    keyword = "/start"

    async def execute(self, cmd: CommandContext) -> None:
        await cmd.store.add_subscriber(cmd.chat_id)
        await cmd.telegram.send_message(cmd.chat_id, WELCOME)


class StopCommand(ICommand):
    keyword = "/stop"

    async def execute(self, cmd: CommandContext) -> None:
        await cmd.store.remove_subscriber(cmd.chat_id)
        await cmd.telegram.send_message(cmd.chat_id, GOODBYE)


class HelpCommand(ICommand):
    """Also the fallback for unknown commands."""

    keyword = "/help"

    async def execute(self, cmd: CommandContext) -> None:
        await cmd.telegram.send_message(cmd.chat_id, help_text(), parse_mode="HTML")


class CommandRouter:
    """Parses an inbound Telegram update and dispatches it to a Command."""

    def __init__(self, commands: Iterable[ICommand], fallback: ICommand) -> None:
        self._commands: dict[str, ICommand] = {c.keyword: c for c in commands}
        self._fallback = fallback

    def register(self, command: ICommand) -> None:
        """Add (or replace) a command strategy."""
        self._commands[command.keyword] = command

    def resolve(self, keyword: str) -> ICommand:
        return self._commands.get(keyword, self._fallback)

    async def handle_update(self, update: TelegramUpdate, store: Store, telegram: TelegramClient) -> None:
        message = update.effective_message
        if message is None or not message.text:
            return

        word, _, args = message.text.strip().partition(" ")
        keyword = word.split("@", 1)[0].lower() # "/start@MyBot" -> "/start"

        cmd = CommandContext(
            chat_id=message.chat.id, args=args.strip(), store=store, telegram=telegram
        )
        await self.resolve(keyword).execute(cmd)
