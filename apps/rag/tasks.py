import uuid
from celery import shared_task
from django.core.files.base import ContentFile

from apps.search.models import ResearchQuery, SourceDocument
from apps.search.searxng_client import search, SearXNGError
from apps.search.scraper import fetch_clean_text
from apps.rag.chunking import chunk_text
from apps.rag.vectorstore import add_chunks, query_chunks
from apps.rag.generator import generate_answer
from apps.reports.models import Report
from apps.reports.exporters import build_markdown, markdown_to_pdf_bytes, markdown_to_docx_bytes


@shared_task(bind=True)
def run_research_pipeline(self, query_id: str):
    rq = ResearchQuery.objects.get(id=query_id)
    try:
        # 1. SEARCH
        rq.status = "searching"
        rq.save(update_fields=["status"])
        results = search(rq.question)

        if not results:
            rq.status = "failed"
            rq.error_message = "SearXNG returned no results."
            rq.save(update_fields=["status", "error_message"])
            return

        # 2. SCRAPE
        rq.status = "scraping"
        rq.save(update_fields=["status"])
        sources = []
        for r in results:
            text = fetch_clean_text(r["url"])
            src = SourceDocument.objects.create(
                query=rq,
                title=r["title"],
                url=r["url"],
                snippet=r["snippet"],
                full_text=text,
                scraped_ok=bool(text),
            )
            sources.append(src)

        # 3. CHUNK + EMBED
        rq.status = "embedding"
        rq.save(update_fields=["status"])
        all_chunks = []
        for src in sources:
            content = src.full_text or src.snippet
            if not content:
                continue
            for piece in chunk_text(content):
                all_chunks.append({
                    "id": str(uuid.uuid4()),
                    "text": piece,
                    "source_id": str(src.id),
                    "source_url": src.url,
                    "source_title": src.title,
                })
        add_chunks(str(rq.id), all_chunks)

        # 4. RETRIEVE + GENERATE (citation engine)
        rq.status = "generating"
        rq.save(update_fields=["status"])
        retrieved = query_chunks(str(rq.id), rq.question)
        result = generate_answer(rq.question, retrieved)

        # 5. BUILD REPORT (markdown + pdf + docx)
        markdown_report = build_markdown(rq.question, result["answer"], result["references"])
        pdf_bytes = markdown_to_pdf_bytes(markdown_report)
        docx_bytes = markdown_to_docx_bytes(rq.question, result["answer"], result["references"])

        report, _ = Report.objects.update_or_create(
            query=rq,
            defaults={
                "answer_markdown": markdown_report,
                "references_json": result["references"],
            },
        )
        report.pdf_file.save(f"{rq.id}.pdf", ContentFile(pdf_bytes), save=False)
        report.docx_file.save(f"{rq.id}.docx", ContentFile(docx_bytes), save=False)
        report.save()

        rq.status = "done"
        rq.save(update_fields=["status"])

    except SearXNGError as e:
        rq.status = "failed"
        rq.error_message = str(e)
        rq.save(update_fields=["status", "error_message"])
    except Exception as e:
        rq.status = "failed"
        rq.error_message = f"Unexpected error: {e}"
        rq.save(update_fields=["status", "error_message"])
        raise
