from django.urls import path
from apps.submissions.views.submission_views import SubmissionDetailView

app_name = 'submissions'

urlpatterns = [
    path('<uuid:pk>/', SubmissionDetailView.as_view(), name='detail'),
]
