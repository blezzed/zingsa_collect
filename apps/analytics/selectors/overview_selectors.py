from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.utils import timezone

from apps.forms.models import Form
from apps.mediafiles.models import MediaFile
from apps.projects.models import Project
from apps.submissions.models import SubmissionIndex

User = get_user_model()


def get_system_overview() -> dict:
    """System-wide aggregates for the superuser dashboard."""
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    projects_by_status = {
        row["status"]: row["count"]
        for row in Project.objects.values("status").annotate(count=Count("id"))
    }

    media = MediaFile.objects.aggregate(
        storage_bytes=Sum("file_size"),
        file_count=Count("id"),
    )

    top_projects = list(
        Project.objects.annotate(submission_count=Count("submissions"))
        .order_by("-submission_count", "-updated_at")
        .values("id", "name", "code", "status", "submission_count")[:5]
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

    return {
        "users": {
            "total": User.objects.count(),
            "active": User.objects.filter(is_active=True).count(),
        },
        "projects": {
            "total": Project.objects.count(),
            "by_status": {
                "draft": projects_by_status.get("draft", 0),
                "active": projects_by_status.get("active", 0),
                "archived": projects_by_status.get("archived", 0),
            },
        },
        "forms": {
            "total": Form.objects.count(),
            "published": Form.objects.filter(status="published").count(),
        },
        "submissions": {
            "total": SubmissionIndex.objects.count(),
            "this_month": SubmissionIndex.objects.filter(
                created_at__gte=month_start
            ).count(),
        },
        "storage": {
            "bytes": int(media["storage_bytes"] or 0),
            "file_count": int(media["file_count"] or 0),
        },
        "top_projects": top_projects,
        "top_storage_users": top_storage_users,
        "recent_projects": recent_projects,
    }
