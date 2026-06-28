from app.bot.telegram import TelegramClient
from app.otodom import FinancialDTO, ListingDTO

client = TelegramClient("test-token")


def test_format_full_listing():
    listing = ListingDTO(
        id=1,
        title="Cozy flat",
        url="https://www.otodom.pl/pl/oferta/cozy-flat",
        area_m2=42.5,
        rooms=2,
        total=FinancialDTO(value=3500, currency="PLN"),
        is_private_owner=True,
        location="Mokotów, Warszawa",
        image_url="https://img.example/1.jpg",
    )

    body = client.format_listing(listing)

    assert "Cozy flat" in body
    assert "3 500 PLN" in body
    assert "42.5 m²" in body
    assert "2 rooms" in body
    assert "Mokotów, Warszawa" in body
    assert "private owner" in body
    assert '<a href="https://www.otodom.pl/pl/oferta/cozy-flat">' in body


def test_format_escapes_html():
    listing = ListingDTO(
        id=2,
        title="Flat <b>& cheap</b>",
        url="https://www.otodom.pl/pl/oferta/x?a=1&b=2",
    )

    body = client.format_listing(listing)

    assert "<b>& cheap</b>" not in body
    assert "&lt;b&gt;" in body
    assert "&amp;" in body


def test_format_omits_absent_fields():
    listing = ListingDTO(
        id=3,
        title="Bare listing",
        url="https://www.otodom.pl/pl/oferta/bare",
    )

    body = client.format_listing(listing)

    assert "Bare listing" in body

def test_format_falls_back_to_rent_when_no_total():
    listing = ListingDTO(
        id=4,
        title="Rent only",
        url="https://www.otodom.pl/pl/oferta/rent",
        rent=FinancialDTO(value=2800, currency="PLN"),
    )

    body = client.format_listing(listing)

    assert "2 800 PLN" in body
