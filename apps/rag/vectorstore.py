"""
Thin wrapper around a persistent ChromaDB client.

Each ResearchQuery gets its own collection (named by query id) so that
contexts from different research sessions never bleed into each other,
and collections can be cleaned up independently.
"""
import chromadb
from chromadb.utils import embedding_functions
from django.conf import settings

_client = None
_embedding_fn = None


def get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.VECTORSTORE_DIR)
    return _client


def get_embedding_fn():
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL
        )
    return _embedding_fn


def get_collection(query_id: str):
    client = get_client()
    return client.get_or_create_collection(
        name=f"query_{query_id.replace('-', '')}",
        embedding_function=get_embedding_fn(),
        metadata={"hnsw:space": "cosine"},
    )


def add_chunks(query_id: str, chunks: list[dict]):
    """
    chunks: list of dicts with keys: id, text, source_id, source_url, source_title
    """
    if not chunks:
        return
    collection = get_collection(query_id)
    collection.add(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[
            {
                "source_id": c["source_id"],
                "source_url": c["source_url"],
                "source_title": c["source_title"],
            }
            for c in chunks
        ],
    )


def query_chunks(query_id: str, question: str, top_k: int = None) -> list[dict]:
    top_k = top_k or settings.TOP_K_CHUNKS
    collection = get_collection(query_id)
    if collection.count() == 0:
        return []
    results = collection.query(query_texts=[question], n_results=min(top_k, collection.count()))

    out = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]
    for doc, meta, dist in zip(docs, metas, dists):
        out.append({
            "text": doc,
            "source_id": meta.get("source_id"),
            "source_url": meta.get("source_url"),
            "source_title": meta.get("source_title"),
            "distance": dist,
        })
    return out


def delete_collection(query_id: str):
    client = get_client()
    try:
        client.delete_collection(name=f"query_{query_id.replace('-', '')}")
    except Exception:
        pass
