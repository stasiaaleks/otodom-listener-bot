from pathlib import Path

from app.otodom import ListingDTO, ListingParser

DUMP = Path(__file__).resolve().parent.parent / "local_dumps" / "otodom_page.html"


def test_parse_real_page_returns_listings():
    """The parser handles a real dumped Otodom search page without drifting."""
    html = DUMP.read_text(encoding="utf-8")

    listings = ListingParser().parse_next_data(html)

    assert isinstance(listings, list)
    assert listings, "expected at least one listing in the dumped page"
    assert all(isinstance(item, ListingDTO) for item in listings)

    first = listings[0]
    assert isinstance(first.id, int)
    assert first.title
    assert first.url.startswith("https://www.otodom.pl/")
