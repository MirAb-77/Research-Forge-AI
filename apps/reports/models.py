from django.db import models
from apps.search.models import ResearchQuery


class Report(models.Model):
    query = models.OneToOneField(ResearchQuery, on_delete=models.CASCADE, related_name="report")
    answer_markdown = models.TextField()
    references_json = models.JSONField(default=list)
    pdf_file = models.FileField(upload_to="reports/pdf/", blank=True, null=True)
    docx_file = models.FileField(upload_to="reports/docx/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report for {self.query_id}"
