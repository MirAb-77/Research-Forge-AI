from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404

from apps.search.models import ResearchQuery
from apps.rag.tasks import run_research_pipeline
from .serializers import ResearchQuerySerializer


def landing(request):
    """Project landing page: title, workflow diagram, functionalities."""
    return render(request, "home.html")


def tool(request):
    """The research ledger — the actual working tool."""
    return render(request, "tool.html")


@api_view(["POST"])
def create_research_query(request):
    question = request.data.get("question", "").strip()
    if not question:
        return Response({"error": "question is required"}, status=status.HTTP_400_BAD_REQUEST)

    rq = ResearchQuery.objects.create(question=question)
    run_research_pipeline.delay(str(rq.id))

    return Response(
        {"id": str(rq.id), "status": rq.status},
        status=status.HTTP_202_ACCEPTED,
    )


@api_view(["GET"])
def get_research_query(request, query_id):
    rq = get_object_or_404(ResearchQuery, id=query_id)
    serializer = ResearchQuerySerializer(rq, context={"request": request})
    return Response(serializer.data)
