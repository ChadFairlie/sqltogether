from django.urls import path

from . import views


urlpatterns = [
    path("query/run/", views.run_query, name="run_query"),
    path("projects/<int:project_id>/query-history/", views.query_history, name="query_history"),
]
