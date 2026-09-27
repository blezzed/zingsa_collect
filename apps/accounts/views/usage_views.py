from apps.accounts.permissions import CanManageUsers
from apps.accounts.selectors.usage_selectors import get_user_usage, list_users_storage
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class AccountUsageView(APIView):
    """
    Current user's storage and submission usage.
    GET /api/accounts/usage/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(get_user_usage(request.user))


class UsersStorageView(APIView):
    """
    Per-user uploaded media totals for staff.
    GET /api/accounts/user-storage/
    """

    permission_classes = [CanManageUsers]

    def get(self, request):
        return Response(list_users_storage())
