from django.contrib import admin
from .models import Submission, SubmissionMedia

class SubmissionMediaInline(admin.TabularInline):
    model = SubmissionMedia
    extra = 0
    readonly_fields = ('field_id', 'media_file', 'created_at')

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('client_submission_id', 'form_version', 'status', 'submitted_by', 'created_at')
    list_filter = ('status', 'form_version__form')
    search_fields = ('client_submission_id', 'submitted_by__username')
    readonly_fields = ('client_submission_id', 'form_version', 'answers', 'metadata', 'submitted_by', 'sync_log', 'created_at', 'updated_at')
    inlines = [SubmissionMediaInline]
