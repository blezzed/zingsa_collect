from django.urls import path

from apps.feedback.views.feedback_views import (
    FeedbackDetailView,
    FeedbackListCreateView,
)

app_name = "feedback"

urlpatterns = [
    path("", FeedbackListCreateView.as_view(), name="list_create"),
    path("<uuid:pk>/", FeedbackDetailView.as_view(), name="detail"),
]
