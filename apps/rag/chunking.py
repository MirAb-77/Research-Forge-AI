from django.conf import settings


def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> list[str]:
    """
    Simple sliding-window character chunker. Good enough for RAG over
    scraped article text; swap for a token-aware splitter if you need
    tighter control over LLM context budgets.
    """
    chunk_size = chunk_size or settings.CHUNK_SIZE
    overlap = overlap or settings.CHUNK_OVERLAP

    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        # try to break on a sentence/paragraph boundary near the end
        boundary = text.rfind(". ", start, end)
        if boundary != -1 and boundary > start + chunk_size * 0.5:
            end = boundary + 1
        chunks.append(text[start:end].strip())
        if end == n:
            break
        start = end - overlap
    return [c for c in chunks if c]
