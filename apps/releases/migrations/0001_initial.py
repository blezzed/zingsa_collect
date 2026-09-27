# Generated for apps.releases

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AppRelease",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "platform",
                    models.CharField(
                        choices=[("android", "Android")],
                        db_index=True,
                        default="android",
                        max_length=16,
                    ),
                ),
                ("version_name", models.CharField(max_length=32)),
                ("version_code", models.PositiveIntegerField()),
                ("notes", models.TextField(blank=True, default="")),
                ("file", models.FileField(upload_to="releases/apk/")),
                ("original_name", models.CharField(max_length=255)),
                ("file_size", models.BigIntegerField()),
                ("checksum", models.CharField(blank=True, default="", max_length=64)),
                (
                    "is_published",
                    models.BooleanField(db_index=True, default=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "uploaded_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="app_releases",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "collect_app_release",
                "ordering": ["-version_code", "-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="apprelease",
            constraint=models.UniqueConstraint(
                fields=("platform", "version_code"),
                name="uniq_release_platform_version_code",
            ),
        ),
        migrations.AddConstraint(
            model_name="apprelease",
            constraint=models.UniqueConstraint(
                fields=("platform", "version_name"),
                name="uniq_release_platform_version_name",
            ),
        ),
    ]
