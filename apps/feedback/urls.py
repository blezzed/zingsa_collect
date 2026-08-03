from django.urls import path

from apps.feedback.views.feedback_views import FeedbackListCreateView

app_name = "feedback"

urlpatterns = [
    path("", FeedbackListCreateView.as_view(), name="list_create"),
]
