from django.contrib.auth import get_user_model
from django.db.models import BigIntegerField, Count, IntegerField, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce

from apps.accounts.selectors.usage_selectors import get_user_usage
from apps.organizations.models import OrganizationMember
from apps.projects.models import Project
from apps.submissions.models import SubmissionIndex, SubmissionMedia

User = get_user_model()


def with_submission_stats(queryset):
    """Annotate submission count and attached media bytes without join blow-up."""
    counts = (
        SubmissionIndex.objects.filter(project_id=OuterRef("pk"))
        .order_by()
        .values("project_id")
        .annotate(c=Count("id"))
        .values("c")
    )
    sizes = (
        SubmissionMedia.objects.filter(submission_index__project_id=OuterRef("pk"))
        .order_by()
        .values("submission_index__project_id")
        .annotate(total=Coalesce(Sum("size"), 0))
        .values("total")
    )
    return queryset.annotate(
        submission_count=Coalesce(Subquery(counts, output_field=IntegerField()), 0),
        submission_bytes=Coalesce(Subquery(sizes, output_field=BigIntegerField()), 0),
    )


def get_project_user_filter_profile(user_id: int) -> dict | None:
    """Profile + project counts for the superuser projects user filter."""
    user = User.objects.filter(pk=user_id).first()
    if user is None:
        return None

    owned = Project.objects.filter(owner_id=user.id).count()
    member = (
        Project.objects.filter(members__user_id=user.id)
        .exclude(owner_id=user.id)
        .distinct()
        .count()
    )
    full_name = f"{user.first_name} {user.last_name}".strip()
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email or "",
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "full_name": full_name,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "date_joined": user.date_joined.isoformat() if user.date_joined else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "country": getattr(user, "country", "") or "",
        "city": getattr(user, "city", "") or "",
        "sector": getattr(user, "sector", "") or "",
        "organization_type": getattr(user, "organization_type", "") or "",
        "bio": getattr(user, "bio", "") or "",
        "owned_project_count": owned,
        "member_project_count": member,
    }


def _user_organizations(user) -> list[dict]:
    rows = (
        OrganizationMember.objects.filter(user_id=user.id)
        .select_related("organization")
        .order_by("organization__name")
    )
    return [
        {
            "id": str(row.organization_id),
            "name": row.organization.name,
            "code": row.organization.code,
            "role": row.role,
        }
        for row in rows
    ]


def get_user_profile_by_username(username: str) -> dict | None:
    term = (username or "").strip()
    if not term:
        return None
    user = User.objects.filter(username__iexact=term).first()
    if user is None:
        return None
    profile = get_project_user_filter_profile(user.id)
    if profile is None:
        return None
    profile["organizations"] = _user_organizations(user)
    usage = get_user_usage(user)
    profile["usage"] = usage
    profile["submission_count"] = usage["submissions_total"]
    return profile


def get_project_list_selector(user=None):
    """
    Projects visible to the user: owned, member of, or all if superuser.
    """
    queryset = Project.objects.all().select_related('organization', 'owner')
    if user and not user.is_superuser:
        queryset = queryset.filter(
            Q(owner=user) | Q(members__user=user)
        ).distinct()
    return with_submission_stats(queryset)


def get_project_by_id_selector(project_id: str, user=None) -> Project:
    """
    Project by ID if the user owns it, is a member, or is superuser.
    """
    queryset = Project.objects.filter(id=project_id).select_related('organization', 'owner')
    if user and not user.is_superuser:
        queryset = queryset.filter(
            Q(owner=user) | Q(members__user=user)
        ).distinct()
    return with_submission_stats(queryset).first()
