from django.db.models import Count, Sum
from django.utils import timezone

from apps.mediafiles.models import MediaFile
from apps.submissions.models import SubmissionIndex


def get_user_usage(user) -> dict:
    """Aggregate storage and submission counts for the given user."""
    media = MediaFile.objects.filter(uploaded_by=user).aggregate(
        storage_bytes=Sum("file_size"),
        file_count=Count("id"),
    )

    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    submissions_this_month = SubmissionIndex.objects.filter(
        submitted_by=user,
        created_at__gte=month_start,
    ).count()

    return {
        "storage_bytes": int(media["storage_bytes"] or 0),
        "file_count": int(media["file_count"] or 0),
        "submissions_this_month": submissions_this_month,
    }
