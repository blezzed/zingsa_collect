import calendar
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.analytics.models import DataExportEvent
from apps.forms.models import Form
from apps.mediafiles.models import MediaFile
from apps.projects.models import Project
from apps.submissions.models import SubmissionIndex

User = get_user_model()

MONTHS = 12


def _month_keys(now, months=MONTHS):
    year, month = now.year, now.month
    keys = []
    labels = []
    for _ in range(months):
        keys.append(f"{year:04d}-{month:02d}")
        labels.append(f"{calendar.month_abbr[month]} {year}")
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    keys.reverse()
    labels.reverse()
    return keys, labels


def _month_start(key: str):
    year, month = int(key[:4]), int(key[5:7])
    naive = datetime(year, month, 1)
    if timezone.is_aware(timezone.now()):
        return timezone.make_aware(naive, timezone.get_current_timezone())
    return naive


def _monthly_counts(queryset, field: str, months=MONTHS) -> dict:
    now = timezone.localtime(timezone.now()) if timezone.is_aware(timezone.now()) else timezone.now()
    keys, labels = _month_keys(now, months)
    start = _month_start(keys[0])
    rows = (
        queryset.filter(**{f"{field}__gte": start})
        .annotate(bucket=TruncMonth(field))
        .values("bucket")
        .annotate(count=Count("id"))
    )
    counts = {}
    for row in rows:
        bucket = row["bucket"]
        if bucket is None:
            continue
        if timezone.is_aware(bucket):
            bucket = timezone.localtime(bucket)
        counts[f"{bucket.year:04d}-{bucket.month:02d}"] = int(row["count"] or 0)
    return {
        "labels": labels,
        "values": [counts.get(key, 0) for key in keys],
    }


def _status_counts(queryset, keys: tuple[str, ...]) -> dict:
    raw = {
        row["status"]: int(row["count"])
        for row in queryset.values("status").annotate(count=Count("id"))
    }
    return {key: raw.get(key, 0) for key in keys}


def _disk_usage(app_bytes: int) -> dict:
    backend = "s3" if getattr(settings, "USE_S3", False) else "local"
    candidates = [Path(settings.MEDIA_ROOT), Path(settings.BASE_DIR)]
    if os.name != "nt":
        candidates.append(Path("/"))

    usage = None
    for path in candidates:
        try:
            if backend == "local":
                path.mkdir(parents=True, exist_ok=True)
            usage = shutil.disk_usage(path)
            break
        except OSError:
            continue

    if usage is None:
        return {
            "available": False,
            "backend": backend,
            "total": None,
            "used": None,
            "free": None,
            "collect_bytes": app_bytes,
            "other_bytes": None,
        }

    # Collect files sit on this volume only for local disk storage.
    collect_on_volume = 0 if backend == "s3" else int(app_bytes)
    other = max(int(usage.used) - collect_on_volume, 0)
    return {
        "available": True,
        "backend": backend,
        "total": int(usage.total),
        "used": int(usage.used),
        "free": int(usage.free),
        "collect_bytes": int(app_bytes),
        "other_bytes": other,
    }


def get_system_overview() -> dict:
    """System-wide aggregates for the Ops+ / superuser dashboard."""
    now = timezone.now()
    local_now = timezone.localtime(now) if timezone.is_aware(now) else now
    month_start = local_now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    d1 = now - timedelta(days=1)
    d7 = now - timedelta(days=7)
    d30 = now - timedelta(days=30)
    d90 = now - timedelta(days=90)

    projects_by_status = _status_counts(
        Project.objects.all(), ("draft", "active", "archived")
    )
    forms_by_status = _status_counts(
        Form.objects.all(), ("draft", "published", "archived")
    )

    media = MediaFile.objects.aggregate(
        storage_bytes=Sum("file_size"),
        file_count=Count("id"),
    )
    app_bytes = int(media["storage_bytes"] or 0)

    top_projects = list(
        Project.objects.annotate(submission_count=Count("submissions"))
        .order_by("-submission_count", "-updated_at")
        .values("id", "name", "code", "status", "submission_count")[:8]
    )
    for row in top_projects:
        row["id"] = str(row["id"])

    top_storage_users = list(
        MediaFile.objects.filter(uploaded_by__isnull=False)
        .values("uploaded_by_id", "uploaded_by__username")
        .annotate(
            storage_bytes=Sum("file_size"),
            file_count=Count("id"),
        )
        .order_by("-storage_bytes")[:5]
    )
    for row in top_storage_users:
        row["user_id"] = row.pop("uploaded_by_id")
        row["username"] = row.pop("uploaded_by__username")
        row["storage_bytes"] = int(row["storage_bytes"] or 0)

    recent_projects = list(
        Project.objects.order_by("-updated_at").values(
            "id", "name", "code", "status", "updated_at", "created_at"
        )[:8]
    )
    for row in recent_projects:
        row["id"] = str(row["id"])
        if row.get("updated_at"):
            row["updated_at"] = row["updated_at"].isoformat()
        if row.get("created_at"):
            row["created_at"] = row["created_at"].isoformat()

    exports_by_format = {
        row["export_format"]: int(row["count"])
        for row in DataExportEvent.objects.values("export_format").annotate(
            count=Count("id")
        )
    }

    users_total = User.objects.count()
    users_enabled = User.objects.filter(is_active=True).count()

    return {
        "users": {
            "total": users_total,
            "active": users_enabled,
            "inactive": users_total - users_enabled,
            "logged_in_30d": User.objects.filter(last_login__gte=d30).count(),
            "by_recency": {
                "labels": [
                    "Last 24h",
                    "2–7 days",
                    "8–30 days",
                    "31–90 days",
                    "90+ / never",
                ],
                "values": [
                    User.objects.filter(last_login__gte=d1).count(),
                    User.objects.filter(last_login__gte=d7, last_login__lt=d1).count(),
                    User.objects.filter(last_login__gte=d30, last_login__lt=d7).count(),
                    User.objects.filter(last_login__gte=d90, last_login__lt=d30).count(),
                    User.objects.filter(
                        last_login__isnull=True
                    ).count()
                    + User.objects.filter(last_login__lt=d90).count(),
                ],
            },
            "signups_by_month": _monthly_counts(User.objects.all(), "date_joined"),
        },
        "projects": {
            "total": Project.objects.count(),
            "by_status": projects_by_status,
        },
        "forms": {
            "total": Form.objects.count(),
            "published": forms_by_status.get("published", 0),
            "by_status": forms_by_status,
        },
        "submissions": {
            "total": SubmissionIndex.objects.count(),
            "this_month": SubmissionIndex.objects.filter(
                created_at__gte=month_start
            ).count(),
            "by_month": _monthly_counts(SubmissionIndex.objects.all(), "created_at"),
        },
        "exports": {
            "total": DataExportEvent.objects.count(),
            "this_month": DataExportEvent.objects.filter(
                created_at__gte=month_start
            ).count(),
            "by_month": _monthly_counts(DataExportEvent.objects.all(), "created_at"),
            "by_format": {
                "labels": ["xlsx", "csv", "geojson", "kml", "json", "spss_labels"],
                "values": [
                    exports_by_format.get("xlsx", 0),
                    exports_by_format.get("csv", 0),
                    exports_by_format.get("geojson", 0),
                    exports_by_format.get("kml", 0),
                    exports_by_format.get("json", 0),
                    exports_by_format.get("spss_labels", 0),
                ],
            },
        },
        "storage": {
            "bytes": app_bytes,
            "file_count": int(media["file_count"] or 0),
            "disk": _disk_usage(app_bytes),
        },
        "top_projects": top_projects,
        "top_storage_users": top_storage_users,
        "recent_projects": recent_projects,
    }
