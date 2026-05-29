from django.contrib import admin
from .models import SyncLog

@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'device_id', 'total_received', 'total_success', 'total_failed', 'started_at', 'finished_at')
    list_filter = ('user',)
    search_fields = ('id', 'device_id', 'user__username')
    readonly_fields = ('id', 'user', 'device_id', 'total_received', 'total_success', 'total_failed', 'conflict_count', 'started_at', 'finished_at')
