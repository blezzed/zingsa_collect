from django.urls import path

from apps.analytics.views.overview_views import AnalyticsOverviewView

app_name = "analytics"

urlpatterns = [
    path("overview/", AnalyticsOverviewView.as_view(), name="overview"),
]
