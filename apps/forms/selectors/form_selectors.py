from django.db.models import Count, Q
from apps.forms.models import Form


def get_form_list_by_project_selector(project_id: str, user=None):
    """
    Forms inside a project visible to owner/members/superuser.
    """
    queryset = Form.objects.filter(project_id=project_id).select_related(
        'project', 'current_version', 'created_by'
    ).annotate(submission_count=Count('submissions', distinct=True))
    if user and not user.is_superuser:
        queryset = queryset.filter(
            Q(project__owner=user) | Q(project__members__user=user)
        ).distinct()
    return queryset


def get_form_by_id_selector(form_id: str, user=None) -> Form:
    """
    Form by ID if user owns/is member of the project, or is superuser.
    """
    queryset = Form.objects.filter(id=form_id).select_related(
        'project', 'current_version', 'created_by'
    ).annotate(submission_count=Count('submissions', distinct=True))
    if user and not user.is_superuser:
        queryset = queryset.filter(
            Q(project__owner=user) | Q(project__members__user=user)
        ).distinct()
    return queryset.first()
