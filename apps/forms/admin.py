from django.contrib import admin
from .models import Form, FormVersion, FormFieldType

class FormVersionInline(admin.TabularInline):
    model = FormVersion
    extra = 0
    fields = ('version_number', 'version_label', 'is_published', 'published_at')
    readonly_fields = ('version_number', 'version_label', 'schema', 'checksum', 'column_mapping', 'physical_table_name')

@admin.register(Form)
class FormAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'status', 'mode', 'created_by', 'created_at')
    list_filter = ('status', 'mode', 'project')
    search_fields = ('title', 'slug', 'description')
    readonly_fields = ('slug',)
    inlines = [FormVersionInline]

@admin.register(FormVersion)
class FormVersionAdmin(admin.ModelAdmin):
    list_display = ('form', 'version_label', 'is_published', 'published_at')
    list_filter = ('is_published',)
    search_fields = ('form__title',)
    readonly_fields = ('schema', 'checksum', 'column_mapping', 'physical_table_name')

@admin.register(FormFieldType)
class FormFieldTypeAdmin(admin.ModelAdmin):
    list_display = ('label', 'name', 'category', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'label', 'description')
    ordering = ('category', 'name')
