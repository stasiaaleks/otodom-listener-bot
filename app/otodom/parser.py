import json
from datetime import datetime

from bs4 import BeautifulSoup

from .models import ROOMS, ListingDTO, FinancialDTO

# props.pageProps.data.searchAds.items
LISTINGS_PATH = ("props", "pageProps", "data", "searchAds", "items")
BASE = "https://www.otodom.pl/"


class ParseError(Exception):
  """Raised when the HTML page does not contain a valid __NEXT_DATA__."""    
  
class ListingParser:
    def parse_next_data(self, html: str) -> list[ListingDTO]:
        """Extract the listings array from a search-results page's __NEXT_DATA__."""
        soup = BeautifulSoup(html, "html.parser")
        tag = soup.find("script", id="__NEXT_DATA__")
        if not tag or not tag.string:
            # No embedded state usually means a challenge/interstitial, not results.
            raise ParseError("__NEXT_DATA__ not found")

        node = json.loads(tag.string)
        for key in LISTINGS_PATH:
            node = node[key]
        return [self._to_listing(item) for item in node]


    def _to_listing(self, it: dict) -> ListingDTO:
        return ListingDTO(
            id=it["id"],
            title=(it.get("title") or "").strip(" ,"),
            url=self._url(it),
            area_m2=it.get("areaInSquareMeters"),
            rooms=self._rooms(it),
            rent=self._money(it.get("rentPrice")),
            total=self._money(it.get("totalPrice")),
            is_private_owner=bool(it.get("isPrivateOwner")),
            location=self._location(it.get("location")),
            image_url=self._first_image(it.get("images")),
            created_at=self._datetime(it.get("dateCreated") or it.get("createdAtFirst")),
            short_description=(it.get("shortDescription") or "").strip() or None,
        )


    def _url(self, it: dict) -> str:
        slug = it.get("slug")
        if slug:
            return f"{BASE}pl/oferta/{slug}"
        href = (it.get("href") or "").replace("[lang]", "pl").replace("/ad/", "/oferta/")
        return BASE + href.lstrip("/")

    def _rooms(self, it: dict) -> int | None:
        rooms_number = it.get("roomsNumber")
        if isinstance(rooms_number, str):
            return ROOMS.get(rooms_number)
        return None

    def _money(self, d: dict | None) -> FinancialDTO | None:
        if not isinstance(d, dict):
            return None
        return FinancialDTO(value=d.get("value"), currency=d.get("currency"))


    def _location(self, d: dict | None) -> str | None:
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


    def _first_image(self, images: list | None) -> str | None:
        if not images:
            return None
        img = images[0]
        if isinstance(img, str):
            return img
        if isinstance(img, dict):
            return img.get("large") or img.get("medium") or img.get("small")
        return None


    def _datetime(self, s: str | None) -> datetime | None:
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
