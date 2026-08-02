from django.urls import path
from . import views

urlpatterns = [
    path("query", views.create_research_query, name="create_query"),
    path("query/<uuid:query_id>", views.get_research_query, name="get_query"),
]
