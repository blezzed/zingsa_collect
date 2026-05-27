from apps.projects.models import Project

def get_project_list_selector(user=None):
    """
    Returns query set of Projects. Superuser sees all, owner sees owned.
    """
    queryset = Project.objects.all().select_related('organization', 'owner')
    if user and not user.is_superuser:
        queryset = queryset.filter(owner=user)
    return queryset


def get_project_by_id_selector(project_id: str, user=None) -> Project:
    """
    Retrieves project by ID. Enforces ownership if not superuser.
    """
    queryset = Project.objects.filter(id=project_id).select_related('organization', 'owner')
    if user and not user.is_superuser:
        queryset = queryset.filter(owner=user)
    return queryset.first()
