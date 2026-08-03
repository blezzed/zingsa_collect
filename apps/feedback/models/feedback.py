import uuid

from django.conf import settings
from django.db import models


class Feedback(models.Model):
    class Category(models.TextChoices):
        BUG = "bug", "Bug"
        IMPROVEMENT = "improvement", "Improvement"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="feedback_items",
    )
    category = models.CharField(
        max_length=32,
        choices=Category.choices,
        default=Category.IMPROVEMENT,
    )
    subject = models.CharField(max_length=200)
    message = models.TextField()
    page_url = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "collect_feedback"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} ({self.get_category_display()})"
