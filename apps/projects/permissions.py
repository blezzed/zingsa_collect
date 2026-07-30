"""DRF permission helpers based on project privilege keys."""

from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

from apps.forms.selectors.form_selectors import get_form_by_id_selector
from apps.projects.selectors.project_selectors import get_project_by_id_selector
from apps.projects.privileges import user_has_project_privilege


class HasProjectPrivilege(BasePermission):
    """
    Requires a specific privilege key on the project from URL kwargs.
    Set `required_privilege` on the view, or pass via constructor.
    """

    privilege = None

    def __init__(self, privilege: str | None = None):
        if privilege:
            self.privilege = privilege

    def has_permission(self, request, view):
        privilege = getattr(view, "required_privilege", None) or self.privilege
        if not privilege:
            return False
        if not request.user or not request.user.is_authenticated:
            return False

        project = None
        project_id = view.kwargs.get("project_id")
        if project_id:
            project = get_project_by_id_selector(project_id, user=request.user)
        else:
            form_id = view.kwargs.get("pk")
            if form_id:
                form = get_form_by_id_selector(form_id, user=request.user)
                project = getattr(form, "project", None) if form else None

        if not project:
            # Let the view return 404 when the object is missing.
            return True

        if not user_has_project_privilege(request.user, project, privilege):
            raise PermissionDenied(
                f"Missing project privilege: {privilege}."
            )
        return True
