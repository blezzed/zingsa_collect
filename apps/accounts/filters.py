import django_filters
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class UserSearchFilter(django_filters.FilterSet):
    """Suggest users by username, name, or email (`?q=`)."""

    q = django_filters.CharFilter(method="filter_q")

    class Meta:
        model = User
        fields = []

    def filter_q(self, queryset, name, value):
        term = (value or "").strip()
        if not term:
            return queryset.none()
        return queryset.filter(
            Q(username__icontains=term)
            | Q(first_name__icontains=term)
            | Q(last_name__icontains=term)
            | Q(email__icontains=term)
        )
