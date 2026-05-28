from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.forms.selectors.form_selectors import get_form_by_id_selector
from apps.submissions.selectors.submission_selectors import get_submission_details_selector
from apps.submissions.serializers.submission_serializers import SubmissionIndexSerializer
from common.view_helpers import raise_if_missing

from apps.submissions.services.web_data_services import (
    get_web_geojson_service,
    get_web_columns_service,
    get_web_paginated_data_service
)


class WebGeoJsonView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, form_id):
        form = raise_if_missing(
            get_form_by_id_selector(form_id, user=request.user),
            'Form not found.'
        )
        data = get_web_geojson_service(form, user=request.user)
        return Response(data)


class WebColumnsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, form_id):
        form = raise_if_missing(
            get_form_by_id_selector(form_id, user=request.user),
            'Form not found.'
        )
        columns = get_web_columns_service(form)
        return Response(columns)


class WebDataPaginatedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, form_id):
        form = raise_if_missing(
            get_form_by_id_selector(form_id, user=request.user),
            'Form not found.'
        )
        
        try:
            page = int(request.query_params.get('page', 1))
            limit = int(request.query_params.get('limit', 50))
        except ValueError:
            page = 1
            limit = 50
            
        data = get_web_paginated_data_service(form, page=page, limit=limit, user=request.user)
        return Response(data)


class WebDataDetailView(APIView):
    """Reuses the existing detail selector, but maps it clearly in the web namespace."""
    permission_classes = [IsAuthenticated]

    def get(self, request, form_id, row_id):
        # We ensure they have access to the form first
        raise_if_missing(
            get_form_by_id_selector(form_id, user=request.user),
            'Form not found.'
        )
        # Note: row_id is physical row id, but our selector currently takes submission_uuid/index_id.
        # Actually, in a web flow, they might click on the physical table 'id'.
        # Let's adjust this to fetch by physical row ID, or we assume row_id = submission_index_id.
        # For simplicity, if we need it by physical ID, we must find the SubmissionIndex.
        from apps.submissions.models import SubmissionIndex
        try:
            sub_index = SubmissionIndex.objects.get(form_id=form_id, physical_row_id=row_id)
            details = raise_if_missing(
                get_submission_details_selector(str(sub_index.id)),
                'Submission not found.'
            )
            meta_serializer = SubmissionIndexSerializer(details['metadata'])
            return Response({
                'metadata': meta_serializer.data,
                'answers': details['answers'],
            })
        except SubmissionIndex.DoesNotExist:
            return Response({"detail": "Submission not found."}, status=404)
