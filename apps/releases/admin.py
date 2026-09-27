from django.contrib import admin

from apps.releases.models import AppRelease


@admin.register(AppRelease)
class AppReleaseAdmin(admin.ModelAdmin):
    list_display = (
        "version_name",
        "version_code",
        "platform",
        "file_size",
        "is_published",
        "uploaded_by",
        "created_at",
    )
    search_fields = ("version_name", "original_name", "notes")
    list_filter = ("platform", "is_published", "created_at")
    readonly_fields = (
        "id",
        "file_size",
        "checksum",
        "original_name",
        "created_at",
    )
