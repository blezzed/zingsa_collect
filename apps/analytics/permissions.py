from rest_framework.permissions import BasePermission

from apps.accounts.permissions import CanViewSystemOverview

# Backward-compatible alias used by analytics urls/views.
IsSuperuser = CanViewSystemOverview


class CanViewAnalyticsOverview(CanViewSystemOverview):
    """Alias for system overview capability."""

    pass
