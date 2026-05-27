import uuid
from django.db import models
from django.conf import settings

class SubmissionIndex(models.Model):
    SYNC_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('synced', 'Synced'),
        ('failed', 'Failed'),
        ('duplicate', 'Duplicate'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    form = models.ForeignKey(
        'forms.Form',
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    form_version = models.ForeignKey(
        'forms.FormVersion',
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submissions'
    )
    device_id = models.CharField(max_length=255)
    client_submission_id = models.CharField(max_length=255)
    physical_table_name = models.CharField(max_length=255)
    physical_row_id = models.IntegerField()
    sync_status = models.CharField(max_length=50, choices=SYNC_STATUS_CHOICES, default='synced')
    synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'collect_submission_index'
        unique_together = ('device_id', 'client_submission_id', 'form')
        ordering = ['-created_at']

    def __str__(self):
        return f"Submission {self.client_submission_id} ({self.sync_status})"


class SubmissionMedia(models.Model):
    FILE_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('voice', 'Voice'),
        ('signature', 'Signature'),
        ('file', 'File'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission_index = models.ForeignKey(
        SubmissionIndex,
        on_delete=models.CASCADE,
        related_name='media_files'
    )
    field_id = models.CharField(max_length=255)
    file = models.FileField(upload_to='submissions/media/', null=True, blank=True)
    file_url = models.URLField(max_length=1000, blank=True, null=True)
    file_type = models.CharField(max_length=50, choices=FILE_TYPE_CHOICES)
    original_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100)
    size = models.IntegerField()
    checksum = models.CharField(max_length=64, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'collect_submission_media'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.field_id} - {self.original_name}"
