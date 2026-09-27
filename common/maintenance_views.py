"""Owner routes that set or clear the maintenance bypass cookie."""

from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from common.maintenance import safe_next, tokens_match


def _read_token(request) -> str:
    return request.POST.get("token") or request.GET.get("token") or ""


def _read_next(request) -> str:
    return request.POST.get("next") or request.GET.get("next") or ""


@csrf_exempt
@require_http_methods(["GET", "POST"])
def maintenance_bypass(request):
    expected = settings.MAINTENANCE_OWNER_TOKEN or ""
    provided = _read_token(request)
    if not tokens_match(expected, provided):
        return HttpResponseForbidden("Invalid maintenance token.")

    response = HttpResponseRedirect(safe_next(_read_next(request)))
    response.set_cookie(
        settings.MAINTENANCE_BYPASS_COOKIE_NAME,
        provided,
        max_age=settings.MAINTENANCE_BYPASS_COOKIE_MAX_AGE,
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite="Lax",
        path="/",
    )
    return response


@csrf_exempt
@require_http_methods(["GET", "POST"])
def maintenance_bypass_clear(request):
    response = HttpResponseRedirect("/")
    response.delete_cookie(
        settings.MAINTENANCE_BYPASS_COOKIE_NAME,
        path="/",
    )
    return response
