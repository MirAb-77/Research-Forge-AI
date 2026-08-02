from rest_framework import serializers
from apps.search.models import ResearchQuery, SourceDocument
from apps.reports.models import Report


class SourceDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceDocument
        fields = ["id", "title", "url", "snippet", "scraped_ok"]


class ReportSerializer(serializers.ModelSerializer):
    pdf_url = serializers.SerializerMethodField()
    docx_url = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = ["answer_markdown", "references_json", "pdf_url", "docx_url", "created_at"]

    def get_pdf_url(self, obj):
        request = self.context.get("request")
        if obj.pdf_file and request:
            return request.build_absolute_uri(obj.pdf_file.url)
        return None

    def get_docx_url(self, obj):
        request = self.context.get("request")
        if obj.docx_file and request:
            return request.build_absolute_uri(obj.docx_file.url)
        return None


class ResearchQuerySerializer(serializers.ModelSerializer):
    sources = SourceDocumentSerializer(many=True, read_only=True)
    report = ReportSerializer(read_only=True)

    class Meta:
        model = ResearchQuery
        fields = ["id", "question", "status", "error_message", "created_at", "sources", "report"]
