"""Rewrite browser-facing MinIO URLs after VPS / firewall changes.

Historical submission JSON stores absolute media URLs captured at upload time,
e.g. http://172.30.5.24:9018/zingsa-collect-media/uploads/...

Client PCs cannot reach :9018. Public media is served via the Django proxy:
  /minio/zingsa-collect-media/...   (same-origin; works for LAN + public IP)
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from django.conf import settings

_BUCKET = "zingsa-collect-media"
_PROXY_PATH_PREFIX = f"/minio/{_BUCKET}/"


def public_media_base() -> str | None:
    """
    Browser-facing media base including bucket, without trailing slash.

    Prefers a same-origin relative base so LAN (172.16.3.24) and external
    (41.174.184.62) clients both work. Absolute CUSTOM_DOMAIN is still honored
    when PUBLIC_MEDIA_RELATIVE is disabled.
    """
    use_relative = os_environ_flag("PUBLIC_MEDIA_RELATIVE", default=True)
    if use_relative:
        return _PROXY_PATH_PREFIX.rstrip("/")

    domain = (getattr(settings, "AWS_S3_CUSTOM_DOMAIN", None) or "").strip().rstrip("/")
    if not domain:
        return _PROXY_PATH_PREFIX.rstrip("/")
    protocol = (getattr(settings, "AWS_S3_URL_PROTOCOL", None) or "http:").rstrip(":")
    if domain.startswith("http://") or domain.startswith("https://"):
        return domain.rstrip("/")
    return f"{protocol}://{domain}"


def os_environ_flag(name: str, default: bool = False) -> bool:
    raw = (getattr(settings, name, None) if hasattr(settings, name) else None)
    if raw is None:
        import os

        raw = os.environ.get(name)
    if raw is None:
        return default
    if isinstance(raw, bool):
        return raw
    return str(raw).strip().lower() in ("1", "true", "yes", "on")


def rewrite_public_media_url(url: str) -> str:
    if not isinstance(url, str) or not url:
        return url
    if _BUCKET not in url and ":9018" not in url and "/minio/" not in url:
        return url

    base = public_media_base()
    if not base:
        return url
    proxy_prefix = base.rstrip("/") + "/"

    # Direct MinIO API port (firewalled) → public proxy path/host.
    rewritten = re.sub(
        rf"https?://[^/\s\"']+:9018/{_BUCKET}/",
        proxy_prefix,
        url,
        flags=re.IGNORECASE,
    )
    # Old / current absolute app hosts → same proxy prefix (relative or configured).
    rewritten = re.sub(
        rf"https?://(?:172\.30\.5\.24|172\.16\.3\.24|41\.174\.184\.62)(?::\d+)?/(?:minio/)?{_BUCKET}/",
        proxy_prefix,
        rewritten,
        flags=re.IGNORECASE,
    )
    # Already-proxied absolute URL on any host → normalize to configured base.
    rewritten = re.sub(
        rf"https?://[^/\s\"']+/(?:minio/)?{_BUCKET}/",
        proxy_prefix,
        rewritten,
        flags=re.IGNORECASE,
    )
    return rewritten


def rewrite_media_urls_in_data(value: Any) -> Any:
    """Deep-rewrite media URL strings inside dict/list JSON payloads."""
    if isinstance(value, str):
        return rewrite_public_media_url(value)
    if isinstance(value, list):
        return [rewrite_media_urls_in_data(item) for item in value]
    if isinstance(value, tuple):
        return tuple(rewrite_media_urls_in_data(item) for item in value)
    if isinstance(value, dict):
        return {key: rewrite_media_urls_in_data(item) for key, item in value.items()}
    return value


def is_direct_minio_url(url: str) -> bool:
    if not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    host = parsed.hostname or ""
    port = parsed.port
    return port == 9018 or host in {"172.30.5.24"}
