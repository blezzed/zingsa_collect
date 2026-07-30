from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from common.view_helpers import raise_if_missing
from apps.projects.permissions import HasProjectPrivilege
from apps.projects.selectors.project_selectors import get_project_by_id_selector
from apps.projects.models.member import ProjectMember
from apps.projects.serializers.member_serializers import (
    ProjectMemberSerializer,
    ProjectMemberCreateSerializer,
    ProjectMemberUpdateSerializer,
)
from apps.projects.services.member_services import (
    add_project_member_service,
    update_project_member_service,
    remove_project_member_service,
)


class ProjectMemberListCreateView(APIView):
    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [IsAuthenticated(), HasProjectPrivilege('view_forms')]
        return [IsAuthenticated(), HasProjectPrivilege('manage_members')]

    def get(self, request, project_id):
        project = raise_if_missing(
            get_project_by_id_selector(project_id, user=request.user),
            'Project not found.'
        )
        members = ProjectMember.objects.filter(project=project).select_related('user', 'project')
        serializer = ProjectMemberSerializer(members, many=True)
        return Response(serializer.data)

    def post(self, request, project_id):
        project = raise_if_missing(
            get_project_by_id_selector(project_id, user=request.user),
            'Project not found.'
        )
        serializer = ProjectMemberCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        member = add_project_member_service(
            project=project,
            username=serializer.validated_data['username'],
            role=serializer.validated_data['role'],
            privilege_overrides=serializer.validated_data.get('privilege_overrides'),
        )
        return Response(ProjectMemberSerializer(member).data, status=status.HTTP_201_CREATED)


class ProjectMemberDetailView(APIView):
    permission_classes = [IsAuthenticated, HasProjectPrivilege]
    required_privilege = "manage_members"

    def patch(self, request, project_id, username):
        project = raise_if_missing(
            get_project_by_id_selector(project_id, user=request.user),
            'Project not found.'
        )
        serializer = ProjectMemberUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        member = update_project_member_service(
            project=project,
            username=username,
            role=serializer.validated_data.get('role'),
            privilege_overrides=serializer.validated_data.get('privilege_overrides')
            if 'privilege_overrides' in serializer.validated_data
            else None,
        )
        return Response(ProjectMemberSerializer(member).data)

    def delete(self, request, project_id, username):
        project = raise_if_missing(
            get_project_by_id_selector(project_id, user=request.user),
            'Project not found.'
        )
        remove_project_member_service(project=project, username=username)
        return Response(status=status.HTTP_204_NO_CONTENT)
