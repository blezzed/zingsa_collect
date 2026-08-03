from rest_framework.permissions import BasePermission


class IsPlatformStaff(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "is_platform_staff", lambda: False)()
        )


class CanViewSystemOverview(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "can_view_system_overview", lambda: False)()
        )


class CanViewAllFeedback(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "can_view_all_feedback", lambda: False)()
        )


class CanManageUsers(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "can_manage_users", lambda: False)()
        )


class CanManageStaff(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "can_manage_staff", lambda: False)()
        )
