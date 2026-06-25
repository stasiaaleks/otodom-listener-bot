class FetchError(RuntimeError):
    """Raised when the search page could not be retrieved (block, timeout, ...)."""


class HTMLPageProvider:
    """Abstracts the retrieval of a search-results HTML page.

    The default implementation uses curl_cffi to impersonate a real Chrome
    fingerprint to get past DataDome.
    """
    
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    async def fetch_search_html(self, url: str, *, timeout: int = 30) -> str:
        """Return the raw HTML of an Otodom search-results page.

        Raises FetchError on a block/challenge or other failure.
        """
        raise NotImplementedError("HTMLPageProvider.fetch_search_html is not implemented yet")