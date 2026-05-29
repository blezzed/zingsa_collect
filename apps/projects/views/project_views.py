from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.projects.selectors.project_selectors import get_project_list_selector, get_project_by_id_selector
from apps.projects.serializers.project_serializers import ProjectSerializer
from apps.projects.services.project_services import create_project_service
from common.view_helpers import raise_if_missing


class ProjectListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        projects = get_project_list_selector(user=request.user)
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = create_project_service(
            name=serializer.validated_data['name'],
            description=serializer.validated_data.get('description'),
            organization=serializer.validated_data.get('organization'),
            owner=request.user,
            status=serializer.validated_data.get('status', 'draft'),
        )
        return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)


class ProjectDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        project = raise_if_missing(
            get_project_by_id_selector(pk, user=request.user),
            'Project not found.',
        )
        return Response(ProjectSerializer(project).data)

    def patch(self, request, pk):
        project = raise_if_missing(
            get_project_by_id_selector(pk, user=request.user),
            'Project not found.',
        )
        serializer = ProjectSerializer(project, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(project, field, value)
        project.full_clean()
        project.save()
        return Response(ProjectSerializer(project).data)

    def delete(self, request, pk):
        project = raise_if_missing(
            get_project_by_id_selector(pk, user=request.user),
            'Project not found.',
        )
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
