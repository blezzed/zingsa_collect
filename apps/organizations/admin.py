from django.contrib import admin
from .models import Organization, OrganizationMember

class OrganizationMemberInline(admin.TabularInline):
    model = OrganizationMember
    extra = 1
    autocomplete_fields = ['user']

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'contact_email', 'phone_number', 'created_at')
    search_fields = ('name', 'code', 'contact_email')
    readonly_fields = ('id', 'code', 'created_at', 'updated_at')
    inlines = [OrganizationMemberInline]
