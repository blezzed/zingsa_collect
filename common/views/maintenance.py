"""Owner bypass endpoints for maintenance mode."""

from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from common.middleware.maintenance import owner_token_valid


def _bypass_cookie_kwargs() -> dict:
    max_age = int(
        getattr(settings, "MAINTENANCE_BYPASS_COOKIE_MAX_AGE", 60 * 60 * 24 * 7)
    )
    secure = bool(getattr(settings, "SESSION_COOKIE_SECURE", False))
    return {
        "max_age": max_age,
        "httponly": True,
        "secure": secure,
        "samesite": "Lax",
    }


@csrf_exempt
@require_http_methods(["GET", "POST"])
def maintenance_bypass_set(request):
    """
    Owner-only: exchange MAINTENANCE_OWNER_TOKEN for a bypass cookie.

    POST form field `token`, or GET ?token=... (POST preferred).
    Optional `next` redirect must start with `/`.
    """
    if request.method == "POST":
        token = (request.POST.get("token") or "").strip()
    else:
        token = (request.GET.get("token") or "").strip()

    if not owner_token_valid(token):
        return HttpResponseForbidden("Invalid maintenance owner token.")

    redirect_to = (
        request.GET.get("next") or request.POST.get("next") or "/"
    ).strip()
    if not redirect_to.startswith("/"):
        redirect_to = "/"

    response = HttpResponseRedirect(redirect_to)
    cookie_name = getattr(
        settings, "MAINTENANCE_BYPASS_COOKIE_NAME", "collect_maintenance_bypass"
    )
    response.set_cookie(cookie_name, token, **_bypass_cookie_kwargs())
    return response


@csrf_exempt
@require_http_methods(["POST", "GET"])
def maintenance_bypass_clear(request):
    """Clear owner maintenance bypass cookie."""
    response = HttpResponseRedirect("/")
    cookie_name = getattr(
        settings, "MAINTENANCE_BYPASS_COOKIE_NAME", "collect_maintenance_bypass"
    )
    response.delete_cookie(cookie_name)
    return response
