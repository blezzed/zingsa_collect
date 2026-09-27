from django.conf import settings
from django.db import models


class DataExportEvent(models.Model):
    """One row per successful form-data download (xlsx/csv/geojson/kml/json/spss)."""

    FORMAT_CHOICES = [
        ("xlsx", "Excel"),
        ("csv", "CSV"),
        ("geojson", "GeoJSON"),
        ("kml", "KML"),
        ("json", "JSON"),
        ("spss_labels", "SPSS labels"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="data_exports",
    )
    form = models.ForeignKey(
        "forms.Form",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="data_exports",
    )
    export_format = models.CharField(max_length=32, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "collect_data_export_event"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at"], name="collect_dat_created_idx"),
        ]

    def __str__(self):
        return f"{self.export_format} export at {self.created_at}"
