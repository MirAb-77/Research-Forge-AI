from django.db import models
import uuid


class ResearchQuery(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("searching", "Searching"),
        ("scraping", "Scraping"),
        ("embedding", "Embedding"),
        ("generating", "Generating"),
        ("done", "Done"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.question[:60]} [{self.status}]"


class SourceDocument(models.Model):
    query = models.ForeignKey(ResearchQuery, on_delete=models.CASCADE, related_name="sources")
    title = models.CharField(max_length=500, blank=True)
    url = models.URLField(max_length=1000)
    snippet = models.TextField(blank=True)
    full_text = models.TextField(blank=True, null=True)
    scraped_ok = models.BooleanField(default=False)
    retrieved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.title or self.url
