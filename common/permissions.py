from rest_framework import permissions
from apps.organizations.models import OrganizationMember
from apps.projects.models import Project, ProjectMember


def _project_from_view(view):
    project_id = view.kwargs.get("project_id")
    if project_id:
        return Project.objects.filter(id=project_id).select_related("organization").first()
    return None


def _is_org_admin_for_project(user, project) -> bool:
    if not project or not project.organization_id:
        return False
    return OrganizationMember.objects.filter(
        organization_id=project.organization_id,
        user=user,
        role="admin",
    ).exists()


class IsOrganizationAdmin(permissions.BasePermission):
    """
    Allows access only to organization admins.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        org_id = view.kwargs.get("org_id")
        if not org_id:
            return True  # Fallback if no org_id in URL, let object permissions handle it

        return OrganizationMember.objects.filter(
            organization_id=org_id,
            user=request.user,
            role="admin",
        ).exists()

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, "organization"):
            org_id = obj.organization.id if obj.organization else None
        elif hasattr(obj, "project") and hasattr(obj.project, "organization"):
            org_id = obj.project.organization.id if obj.project.organization else None
        else:
            org_id = obj.id

        if not org_id:
            return False

        return OrganizationMember.objects.filter(
            organization_id=org_id,
            user=request.user,
            role="admin",
        ).exists()


class IsProjectManagerOrAdmin(permissions.BasePermission):
    """
    Allows access to project owners, project managers, organization admins, or superusers.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True

        project_id = view.kwargs.get("project_id")
        if not project_id:
            return True

        project = _project_from_view(view)
        if not project:
            return False

        if project.owner_id == request.user.id:
            return True

        is_manager = ProjectMember.objects.filter(
            project_id=project_id,
            user=request.user,
            role="manager",
        ).exists()
        if is_manager:
            return True

        return _is_org_admin_for_project(request.user, project)

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        project = getattr(obj, "project", obj) if hasattr(obj, "project") else obj

        if getattr(project, "owner_id", None) == request.user.id:
            return True

        is_manager = ProjectMember.objects.filter(
            project=project,
            user=request.user,
            role="manager",
        ).exists()
        if is_manager:
            return True

        return _is_org_admin_for_project(request.user, project)


class IsProjectCollectorOrHigher(permissions.BasePermission):
    """
    Allows access to project owners, collectors, managers, organization admins, or superusers.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True

        project_id = view.kwargs.get("project_id")
        if not project_id:
            return True

        project = _project_from_view(view)
        if not project:
            return False

        if project.owner_id == request.user.id:
            return True

        is_member = ProjectMember.objects.filter(
            project_id=project_id,
            user=request.user,
        ).exists()
        if is_member:
            return True

        return _is_org_admin_for_project(request.user, project)

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        if hasattr(obj, "form"):
            project = obj.form.project
        elif hasattr(obj, "project"):
            project = obj.project
        else:
            project = obj

        if getattr(project, "owner_id", None) == request.user.id:
            return True

        is_member = ProjectMember.objects.filter(
            project=project,
            user=request.user,
        ).exists()
        if is_member:
            return True

        return _is_org_admin_for_project(request.user, project)
