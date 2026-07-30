import uuid
from django.db import models
from django.conf import settings


class ProjectMember(models.Model):
    ROLE_CHOICES = [
        ('manager', 'Manager'),
        ('collector', 'Data Collector'),
        ('viewer', 'Viewer'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='members'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='project_memberships'
    )
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='collector')
    privilege_overrides = models.JSONField(
        default=dict,
        blank=True,
        help_text='Per-member privilege overrides. Missing keys inherit the role defaults.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'collect_project_member'
        unique_together = ('project', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.project.name} ({self.role})"
