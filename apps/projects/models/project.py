import uuid
from django.db import models
from django.db.models.functions import Lower
from django.conf import settings
from apps.projects.privileges import default_role_privileges


class Project(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='owned_projects'
    )
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='draft')
    # Opt-in. Blank until an owner or manager saves them. Never copied
    # from the owner's account, and not shown to collectors until then.
    contact_name = models.CharField(max_length=150, blank=True, default='')
    contact_phone = models.CharField(max_length=30, blank=True, default='')
    contact_email = models.EmailField(max_length=254, blank=True, default='')
    contact_note = models.CharField(max_length=300, blank=True, default='')
    role_privileges = models.JSONField(
        default=default_role_privileges,
        blank=True,
        help_text='Default privileges per project role (manager/collector/viewer).',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'collect_project'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                Lower('name'),
                'owner',
                name='collect_project_name_owner_ci_uniq',
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"
