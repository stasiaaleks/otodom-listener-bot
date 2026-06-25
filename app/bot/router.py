from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from ..storage import Store
from .schemas import TelegramUpdate
from .telegram import TelegramClient

WELCOME = "You're subscribed — I'll send new Otodom listings as they appear. Send /stop to unsubscribe."
GOODBYE = "You're unsubscribed. Send /start any time to resume."
HELP = "Send /start to subscribe to new listings, or /stop to unsubscribe."


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
        await cmd.telegram.send_message(cmd.chat_id, HELP)


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


# TODO: move to container 
# Default wiring used by the webhook. HelpCommand doubles as the fallback.
_help = HelpCommand()
default_router = CommandRouter(commands=[StartCommand(), StopCommand(), _help], fallback=_help)
