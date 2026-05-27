import uuid
from django.db import models
from django.conf import settings

class SyncLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sync_logs'
    )
    device_id = models.CharField(max_length=255)
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sync_logs'
    )
    form = models.ForeignKey(
        'forms.Form',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sync_logs'
    )
    total_received = models.IntegerField(default=0)
    total_success = models.IntegerField(default=0)
    total_failed = models.IntegerField(default=0)
    conflict_count = models.IntegerField(default=0)
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField()
    log = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = 'collect_sync_log'
        ordering = ['-started_at']

    def __str__(self):
        return f"SyncLog {self.device_id} ({self.total_success}/{self.total_received})"
