from django.db.models import BigIntegerField, Count, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce

from apps.forms.models import Form
from apps.submissions.models import SubmissionMedia


def with_form_submission_stats(queryset):
    """Annotate submission count and attached media bytes without join blow-up."""
    sizes = (
        SubmissionMedia.objects.filter(submission_index__form_id=OuterRef("pk"))
        .order_by()
        .values("submission_index__form_id")
        .annotate(total=Coalesce(Sum("size"), 0))
        .values("total")
    )
    return queryset.annotate(
        submission_count=Count("submissions", distinct=True),
        submission_bytes=Coalesce(Subquery(sizes, output_field=BigIntegerField()), 0),
    )


def get_form_list_by_project_selector(project_id: str, user=None):
    """
    Forms inside a project visible to owner/members/superuser.
    """
    queryset = with_form_submission_stats(
        Form.objects.filter(project_id=project_id).select_related(
            "project", "current_version", "created_by"
        )
    )
    if user and not user.is_superuser:
        queryset = queryset.filter(
            Q(project__owner=user) | Q(project__members__user=user)
        ).distinct()
    return queryset


def get_form_by_id_selector(form_id: str, user=None) -> Form:
    """
    Form by ID if user owns/is member of the project, or is superuser.
    """
    queryset = with_form_submission_stats(
        Form.objects.filter(id=form_id).select_related(
            "project", "current_version", "created_by"
        )
    )
    if user and not user.is_superuser:
        queryset = queryset.filter(
            Q(project__owner=user) | Q(project__members__user=user)
        ).distinct()
    return queryset.first()
