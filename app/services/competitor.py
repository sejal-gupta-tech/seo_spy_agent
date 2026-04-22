import httpx
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

from app.core.config import COMPETITOR_FETCH_TIMEOUT_SECONDS


async def get_top_competitors(keyword: str):
    # Use DuckDuckGo HTML search for more reliable unblocked automated scraping
    query = quote_plus(keyword.strip())
    if not query:
        return []

    search_url = f"https://html.duckduckgo.com/html/?q={query}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        async with httpx.AsyncClient(timeout=COMPETITOR_FETCH_TIMEOUT_SECONDS) as client:
            response = await client.get(search_url, headers=headers)
            response.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    links = []

    for a in soup.select("a.result__url"):
        href = a.get("href")
        # Filter out DuckDuckGo ad links and tracking links
        if href and "http" in href and "duckduckgo.com" not in href:
            if href not in links:  # Avoid duplicates
                links.append(href)

    # Return top 3 competitors (simple version)
    return links[:3]
