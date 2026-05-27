from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from common.permissions import IsProjectManagerOrAdmin, IsProjectCollectorOrHigher

from apps.projects.selectors.project_selectors import get_project_by_id_selector
from apps.forms.selectors.form_selectors import get_form_list_by_project_selector, get_form_by_id_selector
from apps.forms.serializers.form_serializers import FormSerializer
from apps.forms.services.form_services import (
    create_form_service,
    update_form_service,
    publish_form_service,
    get_available_forms_service,
    download_form_definition_service,
)
from common.exceptions import BusinessRuleError
from common.view_helpers import raise_if_missing, require_non_empty_string


class ProjectFormListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsProjectManagerOrAdmin]

    def get(self, request, project_id):
        raise_if_missing(
            get_project_by_id_selector(project_id, user=request.user),
            'Project not found.',
        )
        forms = get_form_list_by_project_selector(project_id, user=request.user)
        serializer = FormSerializer(forms, many=True)
        return Response(serializer.data)

    def post(self, request, project_id):
        project = raise_if_missing(
            get_project_by_id_selector(project_id, user=request.user),
            'Project not found.',
        )
        schema = request.data
        title = require_non_empty_string(schema, 'title', label='Form title')

        form = create_form_service(
            project=project,
            title=title,
            created_by=request.user,
            schema=schema,
            mode=schema.get('mode', 'form_first'),
            geometry_type=schema.get('geometryType', 'none'),
            description=schema.get('description'),
        )
        return Response(FormSerializer(form).data, status=status.HTTP_201_CREATED)


class FormDetailView(APIView):
    permission_classes = [IsAuthenticated, IsProjectManagerOrAdmin]

    def get(self, request, pk):
        form = raise_if_missing(
            get_form_by_id_selector(pk, user=request.user),
            'Form not found.',
        )
        return Response(FormSerializer(form).data)

    def patch(self, request, pk):
        form = raise_if_missing(
            get_form_by_id_selector(pk, user=request.user),
            'Form not found.',
        )
        serializer = FormSerializer(form, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        schema = request.data.get('schema')
        form = update_form_service(
            form=form,
            data=serializer.validated_data,
            schema=schema,
            user=request.user,
        )
        return Response(FormSerializer(form).data)


class FormPublishView(APIView):
    permission_classes = [IsAuthenticated, IsProjectManagerOrAdmin]

    def post(self, request, pk):
        form = raise_if_missing(
            get_form_by_id_selector(pk, user=request.user),
            'Form not found.',
        )
        if not form.current_version:
            raise BusinessRuleError('Form does not have a version to publish.')

        published_version = publish_form_service(form, created_by=request.user)
        return Response({
            'success': True,
            'detail': (
                f"Form '{form.title}' successfully published to table "
                f"'{published_version.physical_table_name}'."
            ),
            'physical_table_name': published_version.physical_table_name,
            'version_number': published_version.version_number,
        })


class AvailableFormsView(APIView):
    permission_classes = [IsAuthenticated, IsProjectCollectorOrHigher]

    def get(self, request):
        project_code = request.query_params.get('project_code')
        forms = get_available_forms_service(project_code=project_code)
        serializer = FormSerializer(forms, many=True)
        return Response(serializer.data)


class FormDownloadView(APIView):
    permission_classes = [IsAuthenticated, IsProjectCollectorOrHigher]

    def get(self, request, pk):
        definition = download_form_definition_service(str(pk))
        return Response(definition)
