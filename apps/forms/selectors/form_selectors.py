from apps.forms.models import Form

def get_form_list_by_project_selector(project_id: str, user=None):
    """
    Returns forms inside a project.
    """
    queryset = Form.objects.filter(project_id=project_id).select_related('project', 'current_version', 'created_by')
    if user and not user.is_superuser:
        queryset = queryset.filter(project__owner=user)
    return queryset


def get_form_by_id_selector(form_id: str, user=None) -> Form:
    """
    Retrieves form by ID. Enforces ownership if not superuser.
    """
    queryset = Form.objects.filter(id=form_id).select_related('project', 'current_version', 'created_by')
    if user and not user.is_superuser:
        queryset = queryset.filter(project__owner=user)
    return queryset.first()
