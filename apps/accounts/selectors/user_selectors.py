from django.contrib.auth import get_user_model

User = get_user_model()


def get_active_users_queryset():
    return User.objects.filter(is_active=True).order_by("username")
