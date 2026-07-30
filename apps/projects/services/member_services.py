from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from apps.projects.models.member import ProjectMember
from apps.projects.privileges import normalize_overrides

User = get_user_model()


def add_project_member_service(
    project,
    username: str,
    role: str,
    privilege_overrides=None,
) -> ProjectMember:
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        raise ValidationError({"username": ["User not found."]})

    overrides = normalize_overrides(privilege_overrides) if privilege_overrides is not None else {}

    member, created = ProjectMember.objects.get_or_create(
        project=project,
        user=user,
        defaults={'role': role, 'privilege_overrides': overrides},
    )

    if not created:
        member.role = role
        if privilege_overrides is not None:
            member.privilege_overrides = overrides
        member.save()

    return member


def update_project_member_service(
    project,
    username: str,
    role: str | None = None,
    privilege_overrides=None,
) -> ProjectMember:
    try:
        member = ProjectMember.objects.get(project=project, user__username=username)
    except ProjectMember.DoesNotExist:
        raise ValidationError({"detail": "Member not found in this project."})

    if role is not None:
        member.role = role
    if privilege_overrides is not None:
        member.privilege_overrides = normalize_overrides(privilege_overrides)
    member.save()
    return member


def remove_project_member_service(project, username: str):
    try:
        member = ProjectMember.objects.get(project=project, user__username=username)
    except ProjectMember.DoesNotExist:
        raise ValidationError({"detail": "Member not found in this project."})

    member.delete()
