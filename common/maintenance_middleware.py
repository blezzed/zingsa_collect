"""HTTP 503 kill switch with an owner token bypass."""

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.deprecation import MiddlewareMixin

from common.maintenance import is_bypass_path, tokens_match, wants_maintenance_json


class MaintenanceModeMiddleware(MiddlewareMixin):
    """When MAINTENANCE_MODE is on, refuse traffic unless the owner token matches."""

    def process_request(self, request):
        if not getattr(settings, "MAINTENANCE_MODE", False):
            return None
        if is_bypass_path(request.path):
            return None

        expected = settings.MAINTENANCE_OWNER_TOKEN or ""
        header = request.headers.get("X-Maintenance-Owner-Token", "")
        cookie_name = settings.MAINTENANCE_BYPASS_COOKIE_NAME
        cookie = request.COOKIES.get(cookie_name, "")
        if tokens_match(expected, header) or tokens_match(expected, cookie):
            return None

        message = settings.MAINTENANCE_MESSAGE
        retry_after = str(settings.MAINTENANCE_RETRY_AFTER)
        if wants_maintenance_json(
            path=request.path,
            accept=request.headers.get("Accept", ""),
            requested_with=request.headers.get("X-Requested-With", ""),
        ):
            response = JsonResponse(
                {"detail": "maintenance", "message": message},
                status=503,
            )
        else:
            response = render(
                request,
                "maintenance.html",
                {"message": message},
                status=503,
            )
        response["Retry-After"] = retry_after
        return response
