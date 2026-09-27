from django.contrib.auth import get_user_model
from django.db.models import (
    BigIntegerField,
    Count,
    IntegerField,
    OuterRef,
    Prefetch,
    Q,
    Subquery,
    Sum,
)
from django.db.models.functions import Coalesce

from apps.mediafiles.models import MediaFile
from apps.organizations.models import OrganizationMember
from apps.projects.models import Project, ProjectMember
from apps.submissions.models import SubmissionIndex
from common.exceptions import ValidationFailed

User = get_user_model()


def _actor_max_assignable_role(actor) -> int:
    role = actor.effective_staff_role()
    if role is None:
        raise ValidationFailed(message="Not allowed to manage staff.")
    return int(role)


def validate_assignable_staff_role(*, actor, staff_role: int) -> int:
    role = int(staff_role)
    valid = {c.value for c in User.StaffRole}
    if role not in valid:
        raise ValidationFailed(
            message="Invalid staff role.",
            errors={"staff_role": ["Choose a valid staff grade."]},
        )

    if role == User.StaffRole.DEVELOPER and not actor.is_developer():
        raise ValidationFailed(
            message="Only Developers can assign the Developer role.",
            errors={"staff_role": ["Only Developers can assign Developer."]},
        )

    max_role = _actor_max_assignable_role(actor)
    if role > max_role:
        raise ValidationFailed(
            message="Cannot assign a grade higher than your own.",
            errors={"staff_role": ["Grade must be at or below your own."]},
        )
    return role


def list_staff_users():
    return (
        User.objects.filter(staff_role__isnull=False)
        .order_by("-staff_role", "username")
    )


def create_staff_user(
    *,
    actor,
    username: str,
    password: str,
    staff_role: int,
    email: str = "",
    first_name: str = "",
    last_name: str = "",
) -> User:
    role = validate_assignable_staff_role(actor=actor, staff_role=staff_role)
    username = (username or "").strip()
    if not username:
        raise ValidationFailed(
            message="Username is required.",
            errors={"username": ["Username is required."]},
        )
    if User.objects.filter(username__iexact=username).exists():
        raise ValidationFailed(
            message="Username already taken.",
            errors={"username": ["Username already taken."]},
        )

    user = User(
        username=username,
        email=(email or "").strip(),
        first_name=(first_name or "").strip(),
        last_name=(last_name or "").strip(),
        staff_role=role,
        is_staff=True,
        is_active=True,
    )
    user.set_password(password)
    user.save()
    return user


def update_staff_user(*, actor, user: User, **fields) -> User:
    if user.staff_role is None:
        raise ValidationFailed(message="User is not platform staff.")

    # Non-developers cannot edit Developers or change anyone to exceed own grade.
    if user.staff_role == User.StaffRole.DEVELOPER and not actor.is_developer():
        raise ValidationFailed(message="Only Developers can edit Developer accounts.")

    if "staff_role" in fields and fields["staff_role"] is not None:
        fields["staff_role"] = validate_assignable_staff_role(
            actor=actor, staff_role=fields["staff_role"]
        )

    for key in ("first_name", "last_name", "email"):
        if key in fields and fields[key] is not None:
            setattr(user, key, str(fields[key]).strip())

    if "is_active" in fields and fields["is_active"] is not None:
        if user.id == actor.id and fields["is_active"] is False:
            raise ValidationFailed(message="You cannot deactivate your own account.")
        user.is_active = bool(fields["is_active"])

    if "staff_role" in fields and fields["staff_role"] is not None:
        user.staff_role = fields["staff_role"]
        user.is_staff = True

    password = fields.get("password")
    if password:
        user.set_password(password)

    user.save()
    return user


def list_end_users(*, search: str = ""):
    qs = User.objects.filter(staff_role__isnull=True, is_superuser=False).order_by(
        "username"
    )
    q = (search or "").strip()
    if q:
        qs = qs.filter(
            Q(username__icontains=q)
            | Q(email__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(country__icontains=q)
            | Q(city__icontains=q)
            | Q(organization_memberships__organization__name__icontains=q)
        ).distinct()
    return _annotate_end_user_stats(qs)


def _annotate_end_user_stats(qs):
    owned = (
        Project.objects.filter(owner_id=OuterRef("pk"))
        .order_by()
        .values("owner_id")
        .annotate(c=Count("id"))
        .values("c")
    )
    members = (
        ProjectMember.objects.filter(user_id=OuterRef("pk"))
        .exclude(project__owner_id=OuterRef("pk"))
        .order_by()
        .values("user_id")
        .annotate(c=Count("id"))
        .values("c")
    )
    storage = (
        MediaFile.objects.filter(uploaded_by_id=OuterRef("pk"))
        .order_by()
        .values("uploaded_by_id")
        .annotate(total=Coalesce(Sum("file_size"), 0))
        .values("total")
    )
    files = (
        MediaFile.objects.filter(uploaded_by_id=OuterRef("pk"))
        .order_by()
        .values("uploaded_by_id")
        .annotate(c=Count("id"))
        .values("c")
    )
    submissions = (
        SubmissionIndex.objects.filter(submitted_by_id=OuterRef("pk"))
        .order_by()
        .values("submitted_by_id")
        .annotate(c=Count("id"))
        .values("c")
    )
    return qs.annotate(
        owned_project_count=Coalesce(Subquery(owned, output_field=IntegerField()), 0),
        member_project_count=Coalesce(Subquery(members, output_field=IntegerField()), 0),
        storage_bytes=Coalesce(Subquery(storage, output_field=BigIntegerField()), 0),
        file_count=Coalesce(Subquery(files, output_field=IntegerField()), 0),
        submission_count=Coalesce(
            Subquery(submissions, output_field=IntegerField()), 0
        ),
    ).prefetch_related(
        Prefetch(
            "organization_memberships",
            queryset=OrganizationMember.objects.select_related(
                "organization"
            ).order_by("organization__name"),
        )
    )


def set_end_user_active(*, actor, user: User, is_active: bool) -> User:
    if user.staff_role is not None or user.is_superuser:
        raise ValidationFailed(
            message="Use the staff team tools to manage platform staff."
        )
    if user.id == actor.id:
        raise ValidationFailed(message="You cannot deactivate your own account.")
    user.is_active = bool(is_active)
    user.save(update_fields=["is_active"])
    return user
