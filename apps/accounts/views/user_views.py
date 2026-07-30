from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.filters import UserSearchFilter
from apps.accounts.selectors.user_selectors import get_active_users_queryset
from apps.accounts.serializers.user_serializers import UserSuggestSerializer


class UserSuggestView(APIView):
    """
    Autocomplete for inviting collaborators.
    GET /api/accounts/users/?q=<term>&limit=8
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = get_active_users_queryset()
        filtered = UserSearchFilter(request.query_params, queryset=queryset).qs

        try:
            limit = int(request.query_params.get("limit", 8))
        except (TypeError, ValueError):
            limit = 8
        limit = max(1, min(limit, 20))

        users = filtered[:limit]
        return Response(UserSuggestSerializer(users, many=True).data)
