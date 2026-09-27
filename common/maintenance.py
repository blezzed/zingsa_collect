"""Owner-bypass maintenance rules. No Django imports."""

import hmac

BYPASS_PATHS = (
    "/__owner/maintenance-bypass/",
    "/__owner/maintenance-bypass/clear/",
)


def tokens_match(expected: str, provided: str) -> bool:
    """Constant-time match. Empty expected or provided tokens never match."""
    if not expected or not provided:
        return False
    return hmac.compare_digest(expected, provided)


def is_bypass_path(path: str) -> bool:
    normalized = path if path.endswith("/") else f"{path}/"
    return normalized in BYPASS_PATHS


def wants_maintenance_json(*, path: str, accept: str, requested_with: str) -> bool:
    if path.startswith("/api/"):
        return True
    if "application/json" in (accept or "").lower():
        return True
    return requested_with == "XMLHttpRequest"


def safe_next(raw: str | None) -> str:
    """Accept only a same-origin path. Anything else goes to /admin/."""
    candidate = (raw or "").strip()
    if candidate.startswith("/") and not candidate.startswith("//"):
        return candidate
    return "/admin/"
