from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "country",
        "sector",
        "is_staff",
        "is_active",
    )
    search_fields = ("username", "email", "first_name", "last_name", "city", "country")
    list_filter = ("is_staff", "is_superuser", "is_active", "newsletter_opt_in", "groups")
    fieldsets = UserAdmin.fieldsets + (
        (
            "Collect profile",
            {
                "fields": (
                    "country",
                    "city",
                    "sector",
                    "organization_type",
                    "bio",
                    "social_linkedin",
                    "newsletter_opt_in",
                )
            },
        ),
    )
