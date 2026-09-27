from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.projects.selectors.project_selectors import get_user_profile_by_username
from common.view_helpers import raise_if_missing


def _can_view_user_profiles(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "is_superuser", False):
        return True
    return bool(getattr(user, "can_manage_users", lambda: False)())


class UserProfileView(APIView):
    """
    GET /api/accounts/profiles/<username>/
    Superuser / user-manager profile for another Collect account.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, username):
        if not _can_view_user_profiles(request.user):
            raise PermissionDenied("You cannot view this profile.")
        profile = raise_if_missing(
            get_user_profile_by_username(username),
            "User not found.",
        )
        return Response(profile)
