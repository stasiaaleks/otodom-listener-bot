from __future__ import annotations

import json
from datetime import datetime

from bs4 import BeautifulSoup

from .models import ROOMS, Listing, Money

# Confirmed by recon: props.pageProps.data.searchAds.items
LISTINGS_PATH = ("props", "pageProps", "data", "searchAds", "items")
BASE = "https://www.otodom.pl/"


def parse_next_data(html: str) -> list[Listing]:
    """Extract the listings array from a search-results page's __NEXT_DATA__."""
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("script", id="__NEXT_DATA__")
    if not tag or not tag.string:
        # No embedded state usually means a challenge/interstitial, not results.
        raise ValueError("__NEXT_DATA__ not found")

    node = json.loads(tag.string)
    for key in LISTINGS_PATH:
        node = node[key]
    return [_to_listing(item) for item in node]


def _to_listing(it: dict) -> Listing:
    return Listing(
        id=it["id"],
        title=(it.get("title") or "").strip(" ,"),
        url=_url(it),
        area_m2=it.get("areaInSquareMeters"),
        rooms=ROOMS.get(it.get("roomsNumber")),
        rent=_money(it.get("rentPrice")),
        total=_money(it.get("totalPrice")),
        is_private_owner=bool(it.get("isPrivateOwner")),
        location=_location(it.get("location")),
        image_url=_first_image(it.get("images")),
        created_at=_dt(it.get("dateCreated") or it.get("createdAtFirst")),
        short_description=(it.get("shortDescription") or "").strip() or None,
    )


def _url(it: dict) -> str:
    href = it.get("href") or f"[lang]/oferta/{it.get('slug', '')}"
    return BASE + href.replace("[lang]", "pl").lstrip("/")


# --- Nested extractors -------------------------------------------------------
# The flat fields above are confirmed from the recon output. The nested shapes
# below (price / location / images) are not yet visible -- VERIFY the key names
# against sample_listing.json and adjust. Each degrades to None rather than
# raising, so the parser stays safe until then.

def _money(d: dict | None) -> Money | None:
    if not isinstance(d, dict):
        return None
    return Money(value=d.get("value"), currency=d.get("currency"))


def _location(d: dict | None) -> str | None:
    if not isinstance(d, dict):
        return None
    addr = d.get("address") or {}
    parts: list[str] = []
    for key in ("street", "district", "city"):
        v = addr.get(key)
        if isinstance(v, dict):
            v = v.get("name")
        if v:
            parts.append(str(v))
    return ", ".join(parts) or None


def _first_image(images: list | None) -> str | None:
    if not images:
        return None
    img = images[0]
    if isinstance(img, str):
        return img
    if isinstance(img, dict):
        return img.get("large") or img.get("medium") or img.get("small")
    return None


def _dt(s: str | None) -> datetime | None:
    if not s:
        return None
    s = s.replace("Z", "+00:00")
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None
