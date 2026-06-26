from fastapi import APIRouter, HTTPException, Request

from ..bot import handle_update
from ..config import settings

router = APIRouter()

# Path Telegram delivers updates to, also used to build the setWebhook URL.
WEBHOOK_PATH = "/telegram/webhook"


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/status")
async def status(request: Request) -> dict:
    # TODO: extend later: last poll time, seen-listing count, subscriber count.
    scheduler = getattr(request.app.state, "scheduler", None)
    return {
        "status": "running",
        "scheduler_running": bool(scheduler and scheduler.running),
    }


@router.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request) -> dict:
    """Inbound Telegram updates (subscribers' /start, /stop, ...)."""

    if settings.webhook_secret:
        sent = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if sent != settings.webhook_secret:
            raise HTTPException(status_code=403, detail="bad webhook secret")

    update = await request.json()
    await handle_update(update, request.app.state.store, request.app.state.telegram)
    return {"ok": True}
