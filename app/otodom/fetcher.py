import asyncio

from curl_cffi import requests as cffi


class FetchError(RuntimeError):
    """Raised when the search page could not be retrieved (block, timeout, ...)."""


class HTMLPageProvider:
    HEADERS = {
        "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    async def fetch_search_html(self, url: str, *, timeout: int = 30) -> str:
        """Return the raw HTML of an Otodom search-results page.
        """
        try:
            resp = await asyncio.to_thread(
                cffi.get,
                url,
                headers=self.HEADERS,
                impersonate="chrome",  # Chrome TLS/HTTP2 fingerprint vs DataDome
                timeout=timeout,
            )
        except Exception as e:
            raise FetchError(f"request to {url} failed: {e}") from e

        if resp.status_code != 200:
            raise FetchError(f"unexpected status {resp.status_code} for {url}")
        return resp.text