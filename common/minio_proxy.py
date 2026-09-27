"""
Same-origin MinIO / S3 object proxy.

Browsers often cannot reach the published MinIO port (9018). Media URLs are
served via the main app port instead, e.g.:

  http://172.16.3.24:8206/minio/zingsa-collect-media/<object-key>

Server-side boto3 continues to use the internal Docker endpoint (minio:9000).
"""

from __future__ import annotations

import logging

import requests
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

# Do not expose MinIO admin / console-style paths through the public proxy.
_BLOCKED_PREFIXES = (
    "minio/",
    "minio-console/",
    ".minio.sys/",
)

_HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "content-encoding",
    "content-length",
}


@csrf_exempt
@require_http_methods(["GET", "HEAD", "OPTIONS"])
def minio_proxy(request, path: str = ""):
    """
    Forward public media GETs to the internal MinIO S3 API.
    """
    if request.method == "OPTIONS":
        response = HttpResponse(status=204)
        response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "*")
        response["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Authorization, Content-Type, Range"
        return response

    normalized = (path or "").lstrip("/")
    if any(normalized.startswith(prefix) for prefix in _BLOCKED_PREFIXES):
        return HttpResponse("Not found", status=404, content_type="text/plain")

    bucket = (getattr(settings, "AWS_STORAGE_BUCKET_NAME", None) or "").strip()
    if bucket and not (
        normalized == bucket or normalized.startswith(f"{bucket}/")
    ):
        return HttpResponse("Not found", status=404, content_type="text/plain")

    base = getattr(
        settings,
        "MINIO_PROXY_UPSTREAM",
        None,
    ) or getattr(
        settings,
        "AWS_S3_ENDPOINT_URL",
        "http://minio:9000",
    )
    base = str(base).rstrip("/")
    upstream = f"{base}/{normalized}" if normalized else base
    query = request.META.get("QUERY_STRING") or ""
    if query:
        upstream = f"{upstream}?{query}"

    headers = {
        "Accept": request.headers.get("Accept", "*/*"),
        "User-Agent": "zingsa-collect-minio-proxy/1.0",
    }
    range_header = request.headers.get("Range")
    if range_header:
        headers["Range"] = range_header

    try:
        upstream_resp = requests.request(
            method=request.method,
            url=upstream,
            headers=headers,
            timeout=(5, 120),
            stream=True,
            allow_redirects=True,
        )
    except requests.RequestException:
        logger.exception("MinIO proxy upstream failed: %s", upstream)
        return HttpResponse("Media storage unavailable", status=502, content_type="text/plain")

    response = HttpResponse(
        upstream_resp.content,
        status=upstream_resp.status_code,
        content_type=upstream_resp.headers.get(
            "Content-Type", "application/octet-stream"
        ),
    )
    for key, value in upstream_resp.headers.items():
        lower = key.lower()
        if lower in _HOP_BY_HOP or lower == "set-cookie":
            continue
        response[key] = value

    response["Access-Control-Allow-Origin"] = "*"
    response["Cache-Control"] = upstream_resp.headers.get(
        "Cache-Control", "public, max-age=300"
    )
    return response
