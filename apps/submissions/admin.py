from django.contrib import admin
from .models import SubmissionIndex, SubmissionMedia


class SubmissionMediaInline(admin.TabularInline):
    model = SubmissionMedia
    extra = 0
    readonly_fields = ('field_id', 'file', 'file_url', 'created_at')


@admin.register(SubmissionIndex)
class SubmissionIndexAdmin(admin.ModelAdmin):
    list_display = (
        'client_submission_id',
        'form_version',
        'sync_status',
        'submitted_by',
        'created_at',
    )
    list_filter = ('sync_status', 'form_version__form')
    search_fields = ('client_submission_id', 'submitted_by__username', 'device_id')
    readonly_fields = (
        'client_submission_id',
        'form_version',
        'project',
        'form',
        'device_id',
        'physical_table_name',
        'physical_row_id',
        'submitted_by',
        'synced_at',
        'created_at',
        'updated_at',
    )
    inlines = [SubmissionMediaInline]


@admin.register(SubmissionMedia)
class SubmissionMediaAdmin(admin.ModelAdmin):
    list_display = ('field_id', 'original_name', 'file_type', 'submission_index', 'created_at')
    list_filter = ('file_type',)
    search_fields = ('field_id', 'original_name', 'submission_index__client_submission_id')
