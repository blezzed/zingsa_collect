from django.conf import settings
from django.db.models import Count, Sum

from apps.analytics.selectors.overview_selectors import _monthly_counts
from apps.mediafiles.models import MediaFile
from apps.submissions.models import SubmissionIndex
from common.exceptions import ValidationFailed

DEFAULT_USER_STORAGE_QUOTA_BYTES = 10 * 1024 * 1024 * 1024


def get_user_storage_quota_bytes() -> int:
    quota = int(
        getattr(settings, "USER_STORAGE_QUOTA_BYTES", DEFAULT_USER_STORAGE_QUOTA_BYTES)
        or DEFAULT_USER_STORAGE_QUOTA_BYTES
    )
    return quota if quota > 0 else DEFAULT_USER_STORAGE_QUOTA_BYTES


def get_user_storage_bytes(user) -> int:
    total = MediaFile.objects.filter(uploaded_by=user).aggregate(
        storage_bytes=Sum("file_size")
    )["storage_bytes"]
    return int(total or 0)


def get_user_usage(user) -> dict:
    """Aggregate storage and submission counts for the given user."""
    media = MediaFile.objects.filter(uploaded_by=user).aggregate(
        storage_bytes=Sum("file_size"),
        file_count=Count("id"),
    )
    used = int(media["storage_bytes"] or 0)
    quota = get_user_storage_quota_bytes()
    remaining = max(quota - used, 0)
    percent = round((used * 1000 / quota) / 10, 1) if quota else 0

    submissions = SubmissionIndex.objects.filter(submitted_by=user)
    by_month = _monthly_counts(submissions, "created_at")
    this_month = by_month["values"][-1] if by_month["values"] else 0

    return {
        "storage_bytes": used,
        "storage_quota_bytes": quota,
        "storage_remaining_bytes": remaining,
        "storage_percent": min(percent, 999.9),
        "file_count": int(media["file_count"] or 0),
        "submissions_this_month": this_month,
        "submissions_total": submissions.count(),
        "submissions_by_month": by_month,
    }


def list_users_storage() -> dict:
    """Per-user uploaded media totals for staff user admin."""
    rows = (
        MediaFile.objects.filter(uploaded_by__isnull=False)
        .values("uploaded_by_id", "uploaded_by__username")
        .annotate(
            storage_bytes=Sum("file_size"),
            file_count=Count("id"),
        )
        .order_by("-storage_bytes")
    )
    users = [
        {
            "user_id": int(row["uploaded_by_id"]),
            "username": row["uploaded_by__username"],
            "storage_bytes": int(row["storage_bytes"] or 0),
            "file_count": int(row["file_count"] or 0),
        }
        for row in rows
    ]
    return {
        "quota_bytes": get_user_storage_quota_bytes(),
        "complete": True,
        "users": users,
    }


def assert_within_storage_quota(user, incoming_bytes: int) -> None:
    """Reject uploads that would take the user over the per-account media cap."""
    quota = get_user_storage_quota_bytes()
    used = get_user_storage_bytes(user)
    incoming = max(int(incoming_bytes or 0), 0)
    if used + incoming <= quota:
        return

    remaining = max(quota - used, 0)
    quota_gb = quota / (1024 * 1024 * 1024)
    quota_label = (
        f"{int(quota_gb)} GB" if quota_gb == int(quota_gb) else f"{quota_gb:.1f} GB"
    )
    raise ValidationFailed(
        message=(
            f"Storage quota exceeded. Each account may store up to {quota_label}. "
            f"{remaining} bytes remaining."
        ),
        code="storage_quota_exceeded",
        errors={
            "file": [
                f"This upload would exceed your {quota_label} storage limit.",
            ],
        },
    )
