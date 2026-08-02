from django.contrib import admin
from .models import ResearchQuery, SourceDocument


class SourceDocumentInline(admin.TabularInline):
    model = SourceDocument
    extra = 0
    readonly_fields = ("title", "url", "scraped_ok", "retrieved_at")


@admin.register(ResearchQuery)
class ResearchQueryAdmin(admin.ModelAdmin):
    list_display = ("question", "status", "created_at")
    list_filter = ("status",)
    inlines = [SourceDocumentInline]


@admin.register(SourceDocument)
class SourceDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "url", "scraped_ok", "query")
