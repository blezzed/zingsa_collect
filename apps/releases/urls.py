from django.urls import path

from apps.releases.views.release_views import (
    ReleaseDetailView,
    ReleaseLatestView,
    ReleaseListCreateView,
)

app_name = "releases"

urlpatterns = [
    path("", ReleaseListCreateView.as_view(), name="list_create"),
    path("latest/", ReleaseLatestView.as_view(), name="latest"),
    path("<uuid:pk>/", ReleaseDetailView.as_view(), name="detail"),
]
