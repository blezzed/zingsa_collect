from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.selectors.usage_selectors import get_user_usage


class AccountUsageView(APIView):
    """
    Current user's storage and submission usage.
    GET /api/accounts/usage/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(get_user_usage(request.user))
