import uuid
from django.db import models
from django.conf import settings

class Form(models.Model):
    MODE_CHOICES = [
        ('form_first', 'Form First'),
        ('map_first', 'Map First'),
    ]

    GEOMETRY_CHOICES = [
        ('none', 'None'),
        ('point', 'Point'),
        ('line', 'Line'),
        ('polygon', 'Polygon'),
        ('mixed', 'Mixed'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='forms'
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField(blank=True, null=True)
    mode = models.CharField(max_length=50, choices=MODE_CHOICES, default='form_first')
    geometry_type = models.CharField(max_length=50, choices=GEOMETRY_CHOICES, default='none')
    current_version = models.ForeignKey(
        'FormVersion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_for_forms'
    )
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='draft')
    is_demo = models.BooleanField(default=False)
    submission_table_name = models.CharField(max_length=255, blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_forms'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'collect_form'
        unique_together = ('project', 'slug')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.slug})"

    @property
    def has_geodata(self):
        """True if the form captures geometry (form-level type or spatial questions)."""
        if self.geometry_type and self.geometry_type != 'none':
            return True
        version = self.current_version
        if not version or not isinstance(getattr(version, 'schema', None), dict):
            return False
        from apps.forms.services.question_schema import schema_has_spatial_questions
        return schema_has_spatial_questions(version.schema.get('questions', []))


class FormVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(
        Form,
        on_delete=models.CASCADE,
        related_name='versions'
    )
    version_number = models.IntegerField()
    version_label = models.CharField(max_length=100)
    schema = models.JSONField()
    checksum = models.CharField(max_length=64)
    is_published = models.BooleanField(default=False)
    physical_table_name = models.CharField(max_length=255, blank=True, null=True)
    column_mapping = models.JSONField(default=dict, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_form_versions'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'collect_form_version'
        unique_together = ('form', 'version_number')
        ordering = ['-version_number']

    def __str__(self):
        return f"{self.form.title} - v{self.version_number} ({self.version_label})"
