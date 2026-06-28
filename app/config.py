from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Otodom encodes room counts as enum tokens, e.g. roomsNumber=[ONE,TWO].
_ROOM_TOKENS = {1: "ONE", 2: "TWO", 3: "THREE", 4: "FOUR", 5: "FIVE", 6: "SIX_OR_MORE"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    bot_token: str
    webhook_secret: str | None = None
    public_url: str | None = None

    search_base_url: str
    price_min: int | None = None
    price_max: int | None = None
    area_min: int | None = None
    area_max: int | None = None
    rooms: list[int] | None = None  # e.g. ROOMS='[2,3]'
    distance_radius: int | None = None  # km around the location
    result_limit: int = 36

    poll_interval_seconds: int = 180

    # Overridden in docker-compose to reach the `db` service by name.
    database_url: str

    @field_validator(
        "price_min", "price_max", "area_min", "area_max", "rooms", "distance_radius",
        mode="before",
    )
    @classmethod
    def _blank_to_none(cls, v):
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

    def build_search_url(self) -> str:
        # TODO: refactor cleaner 
        
        # newest-first 
        params: dict[str, str] = {
            "by": "LATEST",
            "direction": "DESC",
            "limit": str(self.result_limit),
        }
        if self.price_min is not None:
            params["priceMin"] = str(self.price_min)
        if self.price_max is not None:
            params["priceMax"] = str(self.price_max)
        if self.area_min is not None:
            params["areaMin"] = str(self.area_min)
        if self.area_max is not None:
            params["areaMax"] = str(self.area_max)
        if self.distance_radius is not None:
            params["distanceRadius"] = str(self.distance_radius)
        if self.rooms:
            tokens = [_ROOM_TOKENS[r] for r in self.rooms if r in _ROOM_TOKENS]
            if tokens:
                params["roomsNumber"] = f"[{','.join(tokens)}]"

        parts = urlsplit(self.search_base_url)
        merged = dict(parse_qsl(parts.query)) | params
        return urlunsplit(
            (parts.scheme, parts.netloc, parts.path, urlencode(merged), parts.fragment)
        )


settings = Settings() 
