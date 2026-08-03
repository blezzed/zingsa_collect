from django.contrib import admin

from apps.feedback.models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = (
        "subject",
        "category",
        "user",
        "created_at",
    )
    list_filter = ("category", "created_at")
    search_fields = (
        "subject",
        "message",
        "user__username",
        "user__email",
    )
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)
