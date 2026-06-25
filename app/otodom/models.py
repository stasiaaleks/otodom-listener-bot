from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

# Otodom encodes room counts as enum words; map to integers.
ROOMS: dict[str, int] = {
    "ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5,
    "SIX": 6, "SEVEN": 7, "EIGHT": 8, "NINE": 9, "TEN": 10,
}


class FinancialDTO(BaseModel):
    value: float | None = None
    currency: str | None = None


class ListingDTO(BaseModel):
    id: int                       # stable key for the seen-set
    title: str
    url: str
    area_m2: float | None = None
    rooms: int | None = None
    rent: FinancialDTO | None = None     # base rent
    total: FinancialDTO | None = None    # rent + charges
    is_private_owner: bool = False
    location: str | None = None
    image_url: str | None = None
    created_at: datetime | None = None
    short_description: str | None = None
