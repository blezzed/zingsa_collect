from django.contrib import admin
from .models import MediaFile

@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'original_name', 'file_type', 'file_size', 'uploaded_by', 'created_at')
    search_fields = ('original_name', 'file_type')
    list_filter = ('created_at', 'file_type')
    readonly_fields = ('id', 'created_at')
