import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("forms", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DataExportEvent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("export_format", models.CharField(db_index=True, max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "form",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="data_exports",
                        to="forms.form",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="data_exports",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "collect_data_export_event",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="dataexportevent",
            index=models.Index(
                fields=["created_at"], name="collect_dat_created_idx"
            ),
        ),
    ]
