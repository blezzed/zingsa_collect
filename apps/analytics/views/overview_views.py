from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.permissions import IsSuperuser
from apps.analytics.selectors.overview_selectors import get_system_overview


class AnalyticsOverviewView(APIView):
    """
    System-wide ops overview for Ops+ staff.
    GET /api/analytics/overview/
    """

    permission_classes = [IsSuperuser]

    def get(self, request):
        return Response(get_system_overview())
