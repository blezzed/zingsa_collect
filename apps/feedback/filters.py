import django_filters
from django.db.models import Q

from apps.feedback.models import Feedback


class FeedbackFilter(django_filters.FilterSet):
    """Filter feedback with `?search=` and `?category=`."""

    search = django_filters.CharFilter(method="filter_search")
    category = django_filters.ChoiceFilter(choices=Feedback.Category.choices)

    class Meta:
        model = Feedback
        fields = ["category"]

    def filter_search(self, queryset, name, value):
        term = (value or "").strip()
        if not term:
            return queryset
        return queryset.filter(
            Q(subject__icontains=term)
            | Q(message__icontains=term)
            | Q(user__username__icontains=term)
            | Q(page_url__icontains=term)
        )
