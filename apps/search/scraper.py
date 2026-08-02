"""
Fetches and extracts clean readable text from a URL using trafilatura.
Falls back gracefully if extraction fails (paywalled/JS-heavy pages).
"""
import trafilatura


def fetch_clean_text(url: str, timeout: int = 15) -> str | None:
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return None
        text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=True,
            favor_recall=True,
        )
        return text.strip() if text else None
    except Exception:
        return None
