import os
import uuid

from django.conf import settings
from django.db import models


def apk_upload_path(instance, filename):
    ext = os.path.splitext(filename or "")[1].lower() or ".apk"
    name = f"{instance.id}{ext}"
    return os.path.join("releases", "apk", name)


class AppRelease(models.Model):
    class Platform(models.TextChoices):
        ANDROID = "android", "Android"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    platform = models.CharField(
        max_length=16,
        choices=Platform.choices,
        default=Platform.ANDROID,
        db_index=True,
    )
    version_name = models.CharField(max_length=32)
    version_code = models.PositiveIntegerField()
    notes = models.TextField(blank=True, default="")
    file = models.FileField(upload_to=apk_upload_path)
    original_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    checksum = models.CharField(max_length=64, blank=True, default="")
    is_published = models.BooleanField(default=True, db_index=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="app_releases",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "collect_app_release"
        ordering = ["-version_code", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["platform", "version_code"],
                name="uniq_release_platform_version_code",
            ),
            models.UniqueConstraint(
                fields=["platform", "version_name"],
                name="uniq_release_platform_version_name",
            ),
        ]

    def __str__(self):
        return f"{self.get_platform_display()} {self.version_name} ({self.version_code})"
