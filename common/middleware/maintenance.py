"""
Maintenance mode gate for ZINGSA Collect.

When MAINTENANCE_MODE is enabled, public traffic receives HTTP 503.
Owners bypass via header or cookie (see common.views.maintenance).
"""

from __future__ import annotations

import hmac

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.deprecation import MiddlewareMixin


def maintenance_mode_enabled() -> bool:
    return bool(getattr(settings, "MAINTENANCE_MODE", False))


def owner_token_valid(token: str | None) -> bool:
    expected = (getattr(settings, "MAINTENANCE_OWNER_TOKEN", None) or "").strip()
    provided = (token or "").strip()
    if not expected or not provided:
        return False
    return hmac.compare_digest(provided, expected)


def request_has_owner_bypass(request) -> bool:
    header_token = request.headers.get("X-Maintenance-Owner-Token")
    if owner_token_valid(header_token):
        return True
    cookie_name = getattr(
        settings, "MAINTENANCE_BYPASS_COOKIE_NAME", "collect_maintenance_bypass"
    )
    cookie_token = request.COOKIES.get(cookie_name)
    return owner_token_valid(cookie_token)


class MaintenanceModeMiddleware(MiddlewareMixin):
    """
    When MAINTENANCE_MODE=1, block public traffic with HTTP 503.

    Owner bypass (keep full access):
    - Header: X-Maintenance-Owner-Token: <MAINTENANCE_OWNER_TOKEN>
    - Cookie set via GET|POST /__owner/maintenance-bypass/ with field `token`
    - Cookie cleared via GET|POST /__owner/maintenance-bypass/clear/
    """

    BYPASS_PATHS = (
        "/__owner/maintenance-bypass/",
        "/__owner/maintenance-bypass/clear/",
    )

    def process_request(self, request):
        if not maintenance_mode_enabled():
            return None

        path = request.path or "/"
        if path in self.BYPASS_PATHS:
            return None

        if request_has_owner_bypass(request):
            return None

        message = getattr(
            settings,
            "MAINTENANCE_MESSAGE",
            "ZINGSA Collect is temporarily unavailable for maintenance.",
        )
        accept = (request.headers.get("Accept") or "").lower()
        wants_json = (
            path.startswith("/api/")
            or "application/json" in accept
            or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        )
        if wants_json:
            response = JsonResponse(
                {"detail": "maintenance", "message": message},
                status=503,
            )
        else:
            response = render(
                request,
                "maintenance.html",
                {
                    "message": message,
                    "product_name": "ZINGSA Collect",
                },
                status=503,
            )
        response["Retry-After"] = str(
            getattr(settings, "MAINTENANCE_RETRY_AFTER", 300)
        )
        return response
