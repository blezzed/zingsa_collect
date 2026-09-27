import django_filters
from django.db.models import Q

from apps.projects.models import Project


class ProjectFilter(django_filters.FilterSet):
    """Filter projects with `?search=`, `?status=`, and superuser `?user=`."""

    search = django_filters.CharFilter(method="filter_search")
    status = django_filters.ChoiceFilter(choices=Project.STATUS_CHOICES)
    user = django_filters.NumberFilter(method="filter_user")

    class Meta:
        model = Project
        fields = ["status"]

    def filter_search(self, queryset, name, value):
        term = (value or "").strip()
        if not term:
            return queryset
        return queryset.filter(
            Q(name__icontains=term)
            | Q(code__icontains=term)
            | Q(description__icontains=term)
            | Q(organization__name__icontains=term)
        )

    def filter_user(self, queryset, name, value):
        """Superuser-only: projects the given user owns or belongs to."""
        request = getattr(self, "request", None)
        actor = getattr(request, "user", None)
        if not value or not actor or not getattr(actor, "is_superuser", False):
            return queryset
        return queryset.filter(
            Q(owner_id=value) | Q(members__user_id=value)
        ).distinct()
