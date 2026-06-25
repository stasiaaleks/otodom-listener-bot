#!/usr/bin/env python3
"""
Otodom recon test.

PURPOSE
    Determine whether the public search page's embedded __NEXT_DATA__ JSON can be
    retrieved with plain HTTP requests, and reveal the shape of a single listing
    record so the scraper/parser can be built against real field names.

WHERE TO RUN
    Run this ON THE TARGET VM, not on your laptop. Otodom's anti-bot (DataDome)
    decides based on the requesting IP and the client's TLS/HTTP fingerprint, so
    only a run from the deployment IP is representative.

INSTALL
    Preferred (browser TLS/HTTP2 impersonation -- best chance against DataDome):
        pip install curl_cffi beautifulsoup4
    Minimum (lets you see whether a plain client is fingerprint-blocked):
        pip install requests beautifulsoup4

HOW TO READ THE RESULT
    - curl_cffi returns 200 + __NEXT_DATA__ found      -> plain HTTP is viable; build on curl_cffi.
    - curl_cffi blocked but you need data               -> escalate to Playwright (headless browser).
    - 200 but no __NEXT_DATA__ (challenge/interstitial)  -> also a sign you need Playwright.
"""

import json
import sys
from pathlib import Path

# Bulky raw/intermediate dumps land here (gitignored). The curated
# sample_listing.json is written to the repo root as the parser reference.
DUMP_DIR = Path("local_dumps")

# Sort params push newest listings onto page 1. If the dateCreated ordering in
# sample_listing.json is NOT newest-first, adjust/remove these and re-run.
URL = (
    "https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/"
    "dolnoslaskie/wroclaw/wroclaw/wroclaw"
    "?ownerTypeSingleSelect=ALL&by=LATEST&direction=DESC"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}


def fetch_curl_cffi(url):
    from curl_cffi import requests as cffi  # browser-impersonating client
    r = cffi.get(url, headers=HEADERS, impersonate="chrome", timeout=30)
    return r.status_code, r.text


def fetch_requests(url):
    import requests
    r = requests.get(url, headers=HEADERS, timeout=30)
    return r.status_code, r.text


def get_html(url):
    """Try the strongest client first, record every attempt for diagnostics."""
    attempts = []

    # Tier 1 -- real browser TLS/JA3 + HTTP2 fingerprint.
    try:
        code, text = fetch_curl_cffi(url)
        attempts.append(("curl_cffi(impersonate=chrome)", code, len(text)))
        if code == 200 and "__NEXT_DATA__" in text:
            return text, attempts
    except ImportError:
        attempts.append(("curl_cffi", "not installed", 0))
    except Exception as e:  # noqa: BLE001
        attempts.append(("curl_cffi", f"error: {e}", 0))

    # Tier 2 -- plain client. If this is 403 while Tier 1 is 200, the blocker is
    # the TLS fingerprint, confirming curl_cffi (or Playwright) is mandatory.
    try:
        code, text = fetch_requests(url)
        attempts.append(("requests", code, len(text)))
        if code == 200 and "__NEXT_DATA__" in text:
            return text, attempts
    except Exception as e:  # noqa: BLE001
        attempts.append(("requests", f"error: {e}", 0))

    return None, attempts


def extract_next_data(html):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("script", id="__NEXT_DATA__")
    if not tag or not tag.string:
        return None
    return json.loads(tag.string)


def find_listings(node, path="root"):
    """
    Locate the listings array WITHOUT hardcoding a fragile path.
    Heuristic: a list of dicts whose elements carry an 'id' plus at least one
    listing-like field. Returns (json_path, list) for the longest match.
    """
    best = None
    signal = {
        "slug", "title", "totalPrice", "price", "location",
        "areaInSquareMeters", "rentPrice", "roomsNumber",
    }

    if isinstance(node, list):
        if node and isinstance(node[0], dict):
            keys = set(node[0].keys())
            if "id" in keys and keys & signal:
                return path, node
        for i, item in enumerate(node):
            res = find_listings(item, f"{path}[{i}]")
            if res and (best is None or len(res[1]) > len(best[1])):
                best = res
    elif isinstance(node, dict):
        for k, v in node.items():
            res = find_listings(v, f"{path}.{k}")
            if res and (best is None or len(res[1]) > len(best[1])):
                best = res
    return best


def main():
    print(f"Target:\n  {URL}\n")

    DUMP_DIR.mkdir(exist_ok=True)

    html, attempts = get_html(URL)
    print("Fetch attempts (method, status, bytes):")
    for name, code, size in attempts:
        print(f"  - {name}: {code}, {size} bytes")

    if not html:
        print("\nRESULT: page could not be retrieved via HTTP.")
        print("INTERPRETATION: plain HTTP is blocked -> build on Playwright (headless browser).")
        sys.exit(1)

    (DUMP_DIR / "otodom_page.html").write_text(html, encoding="utf-8")
    print(f"\nSaved raw HTML -> {DUMP_DIR}/otodom_page.html ({len(html)} bytes)")

    data = extract_next_data(html)
    if data is None:
        print("RESULT: page retrieved but no __NEXT_DATA__ JSON present.")
        print("INTERPRETATION: likely a challenge/interstitial, not real results -> Playwright.")
        sys.exit(2)

    (DUMP_DIR / "next_data.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Saved parsed __NEXT_DATA__ -> {DUMP_DIR}/next_data.json")

    found = find_listings(data)
    if not found:
        print("RESULT: __NEXT_DATA__ present but no listings array auto-detected.")
        print(f"NEXT: open {DUMP_DIR}/next_data.json and inspect props.pageProps manually.")
        sys.exit(3)

    json_path, listings = found
    print(f"\nListings array found at: {json_path}")
    print(f"Count on first page: {len(listings)}")

    sample = listings[0]
    Path("sample_listing.json").write_text(
        json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("Saved one full listing record -> sample_listing.json\n")

    print("Top-level fields in a single listing record:")
    for k in sorted(sample.keys()):
        v = sample[k]
        preview = v if isinstance(v, (str, int, float, bool, type(None))) else f"<{type(v).__name__}>"
        print(f"  - {k}: {preview}")

    print("\nUse the integer 'id' field as the stable key for the seen-set.")


if __name__ == "__main__":
    main()
