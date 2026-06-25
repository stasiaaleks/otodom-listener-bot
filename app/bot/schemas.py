from __future__ import annotations

from pydantic import BaseModel, ConfigDict

class TelegramChat(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int


class TelegramMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    chat: TelegramChat
    text: str | None = None  # absent for non-text messages (photos, stickers etc)


class TelegramUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    update_id: int | None = None
    message: TelegramMessage | None = None
    edited_message: TelegramMessage | None = None

    @property
    def effective_message(self) -> TelegramMessage | None:
        return self.message or self.edited_message
