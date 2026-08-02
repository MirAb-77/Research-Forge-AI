"""
Citation engine: builds a numbered source list from retrieved chunks,
prompts the LLM to cite every claim with [n] markers referencing ONLY
those sources, then parses the output into (body_text, references[]).
"""
import re
from groq import Groq
from django.conf import settings

SYSTEM_PROMPT = """You are a research assistant that writes well-organized, \
factual answers strictly grounded in the provided sources.

Rules you MUST follow:
1. Use ONLY the information in the numbered sources below. Do not use outside knowledge.
2. Every factual claim must end with a citation marker like [1] or [2][4] referencing \
the source number(s) that support it.
3. If the sources don't contain enough information to answer part of the question, \
say so explicitly instead of guessing.
4. Write in clear prose with short paragraphs or bullet points. No preamble like \
"Based on the sources provided" - just answer directly.
5. Do not invent a References section yourself - that will be generated separately.
"""


def _build_source_block(chunks: list[dict]) -> tuple[str, list[dict]]:
    """
    Deduplicate chunks by source_url, assign each a stable [n] index,
    and build the text block fed to the LLM.
    """
    seen = {}
    order = []
    for c in chunks:
        url = c["source_url"]
        if url not in seen:
            seen[url] = {
                "title": c["source_title"] or url,
                "url": url,
                "excerpts": [],
            }
            order.append(url)
        seen[url]["excerpts"].append(c["text"])

    references = []
    lines = []
    for i, url in enumerate(order, start=1):
        entry = seen[url]
        references.append({"index": i, "title": entry["title"], "url": entry["url"]})
        excerpt_text = "\n---\n".join(entry["excerpts"])
        lines.append(f"[{i}] {entry['title']} ({entry['url']})\n{excerpt_text}")

    return "\n\n".join(lines), references


def generate_answer(question: str, chunks: list[dict]) -> dict:
    """
    Returns {"answer": str, "references": [{"index", "title", "url"}, ...]}
    """
    if not chunks:
        return {
            "answer": "No relevant sources were retrieved for this query. "
                      "Try rephrasing the question or check the search step.",
            "references": [],
        }

    source_block, references = _build_source_block(chunks)

    user_prompt = f"""Question: {question}

Sources:
{source_block}

Write a thorough answer to the question, citing sources with [n] markers as instructed."""

    client = Groq(api_key=settings.GROQ_API_KEY)
    response = client.chat.completions.create(
        model=settings.LLM_MODEL,
        max_tokens=2000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    answer_text = response.choices[0].message.content

    # Keep only references actually cited in the answer text
    cited_indices = {int(n) for n in re.findall(r"\[(\d+)\]", answer_text)}
    used_references = [r for r in references if r["index"] in cited_indices] or references

    return {"answer": answer_text, "references": used_references}
