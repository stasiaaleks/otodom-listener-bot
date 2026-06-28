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
    scheduler = getattr(request.app.state, "scheduler", None)
    store = getattr(request.app.state, "store", None)
    poller = getattr(request.app.state, "poller", None)
    last_poll_at = poller.last_poll_at if poller else None
    return {
        "status": "running",
        "scheduler_running": bool(scheduler and scheduler.running),
        "last_poll_at": last_poll_at.isoformat() if last_poll_at else None,
        "subscribers": await store.count_subscribers() if store else None,
        "seen": await store.count_seen() if store else None,
    }


@router.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request) -> dict:
    if settings.webhook_secret:
        sent = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if sent != settings.webhook_secret:
            raise HTTPException(status_code=403, detail="bad webhook secret")

    update = await request.json()
    await handle_update(update, request.app.state.store, request.app.state.telegram)
    return {"ok": True}
