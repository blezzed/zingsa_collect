from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination

from apps.projects.filters import ProjectFilter
from apps.projects.selectors.project_selectors import get_project_list_selector, get_project_by_id_selector
from apps.projects.serializers.project_serializers import ProjectSerializer
from apps.projects.services.project_services import create_project_service
from apps.projects.permissions import HasProjectPrivilege
from apps.projects.privileges import (
    PRIVILEGE_KEYS,
    PRIVILEGE_LABELS,
    normalize_role_privileges,
    user_has_project_privilege,
)
from apps.projects.serializers.member_serializers import ProjectRolePrivilegesSerializer
from common.view_helpers import raise_if_missing


def _require_project_admin(user, project):
    """Owner or manage_members (managers) may edit/delete the project."""
    if getattr(user, "is_superuser", False):
        return
    if project.owner_id == user.id:
        return
    if user_has_project_privilege(user, project, "manage_members"):
        return
    raise PermissionDenied("You do not have permission to change this project.")


class ProjectPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 100


class ProjectListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = ProjectPagination

    def get(self, request):
        queryset = get_project_list_selector(user=request.user)
        filtered = ProjectFilter(request.query_params, queryset=queryset).qs
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(filtered, request, view=self)
        serializer = ProjectSerializer(
            page, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = ProjectSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        project = create_project_service(
            name=serializer.validated_data['name'],
            description=serializer.validated_data.get('description'),
            organization=serializer.validated_data.get('organization'),
            owner=request.user,
            status=serializer.validated_data.get('status', 'draft'),
        )
        return Response(
            ProjectSerializer(project, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class ProjectDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        project = raise_if_missing(
            get_project_by_id_selector(pk, user=request.user),
            'Project not found.',
        )
        return Response(ProjectSerializer(project, context={'request': request}).data)

    def patch(self, request, pk):
        project = raise_if_missing(
            get_project_by_id_selector(pk, user=request.user),
            'Project not found.',
        )
        _require_project_admin(request.user, project)
        serializer = ProjectSerializer(
            project, data=request.data, partial=True, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(project, field, value)
        project.full_clean()
        project.save()
        return Response(ProjectSerializer(project, context={'request': request}).data)

    def delete(self, request, pk):
        project = raise_if_missing(
            get_project_by_id_selector(pk, user=request.user),
            'Project not found.',
        )
        _require_project_admin(request.user, project)
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectRolePrivilegesView(APIView):
    """GET/PATCH default privileges for manager/collector/viewer roles (Settings)."""

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [IsAuthenticated(), HasProjectPrivilege('view_forms')]
        return [IsAuthenticated(), HasProjectPrivilege('manage_members')]

    def get(self, request, project_id):
        project = raise_if_missing(
            get_project_by_id_selector(project_id, user=request.user),
            'Project not found.',
        )
        return Response({
            'privileges': [
                {'key': key, 'label': PRIVILEGE_LABELS[key]}
                for key in PRIVILEGE_KEYS
            ],
            'role_privileges': normalize_role_privileges(project.role_privileges),
        })

    def patch(self, request, project_id):
        project = raise_if_missing(
            get_project_by_id_selector(project_id, user=request.user),
            'Project not found.',
        )
        serializer = ProjectRolePrivilegesSerializer(
            data=request.data,
            context={'current': project.role_privileges},
        )
        serializer.is_valid(raise_exception=True)
        project.role_privileges = serializer.validated_data
        project.save(update_fields=['role_privileges', 'updated_at'])
        return Response({
            'privileges': [
                {'key': key, 'label': PRIVILEGE_LABELS[key]}
                for key in PRIVILEGE_KEYS
            ],
            'role_privileges': normalize_role_privileges(project.role_privileges),
        })
