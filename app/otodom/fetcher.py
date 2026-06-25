from __future__ import annotations

# curl_cffi impersonates a real Chrome TLS/HTTP2 fingerprint, which is what gets
# us past DataDome (see recon.py). Import is local to fetch() so the module
# stays importable even before the optional client is installed.


class FetchError(RuntimeError):
    """Raised when the search page could not be retrieved (block, timeout, ...)."""


# Browser-like headers; mirrors recon.py. Kept here so fetch() is self-contained.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
}


async def fetch_search_html(url: str, *, timeout: int = 30) -> str:
    """Return the raw HTML of an Otodom search-results page.

    STUB: real implementation will use curl_cffi with impersonate="chrome",
    check the status code, and raise FetchError on a block/challenge.
    """
    raise NotImplementedError("fetcher.fetch_search_html is not implemented yet")
