import django_filters
from django.db.models import Q

from apps.projects.models import Project


class ProjectFilter(django_filters.FilterSet):
    """Filter projects with `?search=` and `?status=`."""

    search = django_filters.CharFilter(method="filter_search")
    status = django_filters.ChoiceFilter(choices=Project.STATUS_CHOICES)

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
