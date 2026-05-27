from rest_framework import permissions
from apps.organizations.models import OrganizationMember
from apps.projects.models import ProjectMember

class IsOrganizationAdmin(permissions.BasePermission):
    """
    Allows access only to organization admins.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        org_id = view.kwargs.get('org_id')
        if not org_id:
            return True # Fallback if no org_id in URL, let object permissions handle it

        return OrganizationMember.objects.filter(
            organization_id=org_id,
            user=request.user,
            role='admin'
        ).exists()

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'organization'):
            org_id = obj.organization.id if obj.organization else None
        elif hasattr(obj, 'project') and hasattr(obj.project, 'organization'):
            org_id = obj.project.organization.id if obj.project.organization else None
        else:
            org_id = obj.id

        if not org_id:
            return False

        return OrganizationMember.objects.filter(
            organization_id=org_id,
            user=request.user,
            role='admin'
        ).exists()


class IsProjectManagerOrAdmin(permissions.BasePermission):
    """
    Allows access to Project Managers or Organization Admins.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        project_id = view.kwargs.get('project_id')
        if not project_id:
            return True

        is_manager = ProjectMember.objects.filter(
            project_id=project_id,
            user=request.user,
            role='manager'
        ).exists()
        
        if is_manager:
            return True
            
        return OrganizationMember.objects.filter(
            organization__projects__id=project_id,
            user=request.user,
            role='admin'
        ).exists()

    def has_object_permission(self, request, view, obj):
        project = getattr(obj, 'project', obj) if hasattr(obj, 'project') else obj
        
        is_manager = ProjectMember.objects.filter(
            project=project,
            user=request.user,
            role='manager'
        ).exists()
        
        if is_manager:
            return True
            
        org = getattr(project, 'organization', None)
        if org:
            return OrganizationMember.objects.filter(
                organization=org,
                user=request.user,
                role='admin'
            ).exists()
            
        return False


class IsProjectCollectorOrHigher(permissions.BasePermission):
    """
    Allows access to Project Data Collectors, Managers, or Organization Admins.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'form'):
            project = obj.form.project
        elif hasattr(obj, 'project'):
            project = obj.project
        else:
            project = obj

        is_member = ProjectMember.objects.filter(
            project=project,
            user=request.user
        ).exists()
        
        if is_member:
            return True
            
        org = getattr(project, 'organization', None)
        if org:
            return OrganizationMember.objects.filter(
                organization=org,
                user=request.user,
                role='admin'
            ).exists()
            
        return False
