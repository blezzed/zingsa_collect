"""Project privilege keys and effective-access helpers."""

from __future__ import annotations

PRIVILEGE_KEYS = (
    "view_forms",
    "create_forms",
    "edit_forms",
    "publish_forms",
    "manage_members",
    "view_data",
    "add_submissions",
)

PRIVILEGE_LABELS = {
    "view_forms": "View forms",
    "create_forms": "Create forms",
    "edit_forms": "Edit forms",
    "publish_forms": "Publish / deploy forms",
    "manage_members": "Manage collaborators",
    "view_data": "View submissions / data",
    "add_submissions": "Add submissions",
}

PROJECT_ROLES = ("manager", "collector", "viewer")

DEFAULT_ROLE_PRIVILEGES = {
    "manager": list(PRIVILEGE_KEYS),
    "collector": [
        "view_forms",
        "view_data",
        "add_submissions",
    ],
    "viewer": [
        "view_forms",
        "view_data",
    ],
}


def default_role_privileges() -> dict:
    return {role: list(DEFAULT_ROLE_PRIVILEGES[role]) for role in PROJECT_ROLES}


def normalize_role_privileges(raw) -> dict:
    base = default_role_privileges()
    if not isinstance(raw, dict):
        return base
    for role in PROJECT_ROLES:
        values = raw.get(role)
        if isinstance(values, list):
            base[role] = [k for k in values if k in PRIVILEGE_KEYS]
    return base


def normalize_overrides(raw) -> dict:
    if not isinstance(raw, dict):
        return {}
    return {
        key: bool(value)
        for key, value in raw.items()
        if key in PRIVILEGE_KEYS
    }


def effective_privileges_for_user(user, project) -> list[str]:
    """Resolved privilege keys for a user on a project."""
    from apps.organizations.models import OrganizationMember
    from apps.projects.models import ProjectMember

    if not user or not user.is_authenticated:
        return []

    if getattr(user, "is_superuser", False) or project.owner_id == user.id:
        return list(PRIVILEGE_KEYS)

    if project.organization_id and OrganizationMember.objects.filter(
        organization_id=project.organization_id,
        user=user,
        role="admin",
    ).exists():
        return list(PRIVILEGE_KEYS)

    member = (
        ProjectMember.objects.filter(project=project, user=user)
        .select_related("user")
        .first()
    )
    if not member:
        return []

    role_map = normalize_role_privileges(getattr(project, "role_privileges", None))
    granted = set(role_map.get(member.role, []))
    overrides = normalize_overrides(getattr(member, "privilege_overrides", None))
    for key, enabled in overrides.items():
        if enabled:
            granted.add(key)
        else:
            granted.discard(key)
    return [key for key in PRIVILEGE_KEYS if key in granted]


def user_has_project_privilege(user, project, privilege: str) -> bool:
    return privilege in effective_privileges_for_user(user, project)
