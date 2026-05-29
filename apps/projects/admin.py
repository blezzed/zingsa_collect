from django.contrib import admin
from .models import Project, ProjectMember

class ProjectMemberInline(admin.TabularInline):
    model = ProjectMember
    extra = 1
    autocomplete_fields = ['user']

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'organization', 'owner', 'status', 'created_at')
    search_fields = ('name', 'code', 'organization__name', 'owner__username')
    list_filter = ('status', 'organization')
    readonly_fields = ('id', 'code', 'created_at', 'updated_at')
    inlines = [ProjectMemberInline]
    autocomplete_fields = ['organization', 'owner']
