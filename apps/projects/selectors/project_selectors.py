from django.db.models import Q
from apps.projects.models import Project


def get_project_list_selector(user=None):
    """
    Projects visible to the user: owned, member of, or all if superuser.
    """
    queryset = Project.objects.all().select_related('organization', 'owner')
    if user and not user.is_superuser:
        queryset = queryset.filter(
            Q(owner=user) | Q(members__user=user)
        ).distinct()
    return queryset


def get_project_by_id_selector(project_id: str, user=None) -> Project:
    """
    Project by ID if the user owns it, is a member, or is superuser.
    """
    queryset = Project.objects.filter(id=project_id).select_related('organization', 'owner')
    if user and not user.is_superuser:
        queryset = queryset.filter(
            Q(owner=user) | Q(members__user=user)
        ).distinct()
    return queryset.first()
