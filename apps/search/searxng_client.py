"""
Thin client around a self-hosted SearXNG instance.

SearXNG must have `formats: [html, json]` enabled in settings.yml
(see searxng-config/settings.yml in this repo) or the JSON endpoint
will 403.
"""
import requests
from django.conf import settings


class SearXNGError(Exception):
    pass


def search(query: str, num_results: int = None, categories: str = "general") -> list[dict]:
    """
    Query SearXNG and return a normalized list of results:
    [{title, url, snippet, engine}, ...]
    """
    num_results = num_results or settings.TOP_K_RESULTS
    params = {
        "q": query,
        "format": "json",
        "categories": categories,
    }
    try:
        resp = requests.get(f"{settings.SEARXNG_URL}/search", params=params, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise SearXNGError(f"SearXNG request failed: {e}") from e

    data = resp.json()
    results = []
    for item in data.get("results", [])[:num_results]:
        results.append({
            "title": item.get("title", "").strip(),
            "url": item.get("url", "").strip(),
            "snippet": item.get("content", "").strip(),
            "engine": item.get("engine", ""),
        })
    return results
