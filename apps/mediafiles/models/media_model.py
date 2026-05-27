import uuid
import os
from django.db import models
from django.conf import settings

def media_upload_path(instance, filename):
    # Upload path format: uploads/YYYY/MM/filename
    return os.path.join('uploads', '%Y', '%m', filename)

class MediaFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to=media_upload_path)
    original_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100)
    file_size = models.BigIntegerField()
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='media_files')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.original_name} ({self.id})"

    class Meta:
        ordering = ['-created_at']
