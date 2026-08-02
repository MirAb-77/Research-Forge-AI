"""
Free web search via DuckDuckGo (using the `ddgs` library).

No server to run, no API key, no rate-limit signup - just pip install ddgs.
Same output shape as the old SearXNG client so nothing downstream changes:
[{title, url, snippet, engine}, ...]
"""
from ddgs import DDGS
from ddgs.exceptions import DDGSException
from django.conf import settings


class SearchError(Exception):
    pass


def search(query: str, num_results: int = None) -> list[dict]:
    num_results = num_results or settings.TOP_K_RESULTS
    try:
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(query, max_results=num_results))
    except DDGSException as e:
        raise SearchError(f"DuckDuckGo search failed: {e}") from e

    results = []
    for item in raw_results:
        results.append({
            "title": (item.get("title") or "").strip(),
            "url": (item.get("href") or "").strip(),
            "snippet": (item.get("body") or "").strip(),
            "engine": "duckduckgo",
        })
    return results
