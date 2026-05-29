from django.db import models

class FormFieldType(models.Model):
    name = models.CharField(max_length=50, unique=True, help_text="The internal JSON type identifier (e.g. 'text', 'polygon')")
    label = models.CharField(max_length=100, help_text="Human-readable label for the UI (e.g. 'Single-line text input')")
    description = models.TextField(blank=True, help_text="Detailed description of the field's purpose")
    category = models.CharField(max_length=50, help_text="Category for grouping in the UI (e.g. 'Basic', 'GIS', 'Media')")
    is_active = models.BooleanField(default=True, help_text="Whether this field type is currently available for form building")
    properties_schema = models.JSONField(default=dict, blank=True, help_text="JSON schema dictating what configuration properties are allowed for this field")
    
    class Meta:
        db_table = 'forms_field_type'
        ordering = ['category', 'name']
        verbose_name = 'Form Field Type'
        verbose_name_plural = 'Form Field Types'

    def __str__(self):
        return f"{self.label} ({self.name})"
