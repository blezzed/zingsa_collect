"""
Serve the Next.js static export from ux_ui/ alongside the Collect API.
"""

from __future__ import annotations

import mimetypes
import re
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponseNotFound
from django.views.decorators.http import require_GET

# Build-time placeholder for dynamic App Router segments.
_SPA_PLACEHOLDER = "_"

_DYNAMIC_RE = re.compile(
    r"^(?P<head>(?:forms|projects)/)(?P<id>[^/]+)(?P<tail>(?:/.*)?)?$"
)


def _ux_root() -> Path | None:
    root = Path(getattr(settings, "UX_UI_ROOT", ""))
    if not getattr(settings, "UX_UI_ENABLED", False):
        return None
    if not root.is_dir():
        return None
    return root.resolve()


def _safe_join(root: Path, relative: str) -> Path | None:
    """Resolve relative path under root; return None if it escapes."""
    relative = relative.replace("\\", "/").lstrip("/")
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def _index_rel(rel: str) -> str:
    rel = rel.strip("/")
    return "index.html" if not rel else f"{rel}/index.html"


def _candidate_files(root: Path, resource: str) -> list[Path]:
    """Ordered file candidates for a request path."""
    resource = (resource or "").replace("\\", "/").lstrip("/")
    seen: set[Path] = set()
    ordered: list[Path] = []

    def add(rel: str) -> None:
        path = _safe_join(root, rel)
        if path is None or path in seen:
            return
        seen.add(path)
        ordered.append(path)

    # Exact file, then directory index
    if resource:
        if not resource.endswith("/"):
            add(resource)
        add(_index_rel(resource))
    else:
        add("index.html")

    # Rewrite /forms/<uuid>/... → /forms/_/...
    normalized = resource.strip("/")
    match = _DYNAMIC_RE.match(normalized) if normalized else None
    if match and match.group("id") != _SPA_PLACEHOLDER:
        tail = match.group("tail") or ""
        placeholder = f"{match.group('head')}{_SPA_PLACEHOLDER}{tail}".strip("/")
        add(placeholder)
        add(_index_rel(placeholder))

    add("index.html")
    return ordered


def _content_type(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(str(path))
    if path.suffix.lower() == ".html":
        return "text/html; charset=utf-8"
    if guessed:
        return guessed
    fallback = {
        ".js": "application/javascript",
        ".mjs": "application/javascript",
        ".css": "text/css",
        ".json": "application/json",
        ".svg": "image/svg+xml",
        ".map": "application/json",
        ".woff": "font/woff",
        ".woff2": "font/woff2",
    }
    return fallback.get(path.suffix.lower(), "application/octet-stream")


@require_GET
def serve_ux_ui(request, resource: str = ""):
    """
    Serve a file from UX_UI_ROOT with SPA fallback for dynamic form/project routes.
    """
    root = _ux_root()
    if root is None:
        raise Http404("Frontend UI is not available.")

    for candidate in _candidate_files(root, resource):
        if candidate.is_file():
            response = FileResponse(
                candidate.open("rb"),
                content_type=_content_type(candidate),
            )
            if candidate.suffix.lower() == ".html":
                response["Cache-Control"] = "no-cache"
            elif "/_next/static/" in candidate.as_posix():
                response["Cache-Control"] = "public, max-age=31536000, immutable"
            return response

    return HttpResponseNotFound("Not found.")
