from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from apps.forms.selectors.form_selectors import get_form_by_id_selector
from apps.submissions.selectors.submission_selectors import get_submission_details_selector
from apps.submissions.serializers.submission_serializers import SubmissionIndexSerializer
from common.view_helpers import raise_if_missing

from apps.submissions.services.web_data_services import (
    get_web_geojson_service,
    get_web_columns_service,
    get_web_paginated_data_service,
    get_web_export_table_service,
    build_csv_bytes,
    build_xlsx_bytes,
    build_json_bytes,
    build_spss_labels_bytes,
    delete_web_row_service,
)


class WebGeoJsonView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, form_id):
        form = raise_if_missing(
            get_form_by_id_selector(form_id, user=request.user),
            "Form not found.",
        )
        data = get_web_geojson_service(form, user=request.user)
        return Response(data)


class WebColumnsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, form_id):
        form = raise_if_missing(
            get_form_by_id_selector(form_id, user=request.user),
            "Form not found.",
        )
        columns = get_web_columns_service(form)
        return Response(columns)


class WebDataPaginatedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, form_id):
        form = raise_if_missing(
            get_form_by_id_selector(form_id, user=request.user),
            "Form not found.",
        )

        try:
            page = int(request.query_params.get("page", 1))
            limit = int(request.query_params.get("limit", 50))
        except ValueError:
            page = 1
            limit = 50

        search = (
            request.query_params.get("search")
            or request.query_params.get("q")
            or ""
        )

        data = get_web_paginated_data_service(
            form,
            page=page,
            limit=limit,
            user=request.user,
            search=search,
        )
        return Response(data)


class WebDataExportView(APIView):
    """
    Kobo-style downloads:
      format=xlsx|csv|geojson|json|spss_labels
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, form_id):
        form = raise_if_missing(
            get_form_by_id_selector(form_id, user=request.user),
            "Form not found.",
        )
        # Prefer export_format; also accept format= (URL_FORMAT_OVERRIDE is None).
        fmt = (
            request.query_params.get("export_format")
            or request.query_params.get("format")
            or "xlsx"
        ).lower().strip()
        slug = getattr(form, "slug", None) or str(form.id)

        if fmt == "geojson":
            payload = get_web_geojson_service(form, user=request.user)
            import json

            content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            response = HttpResponse(content, content_type="application/geo+json")
            response["Content-Disposition"] = f'attachment; filename="{slug}.geojson"'
            return response

        table = get_web_export_table_service(form)

        if fmt == "csv":
            content = build_csv_bytes(table)
            response = HttpResponse(content, content_type="text/csv; charset=utf-8")
            response["Content-Disposition"] = f'attachment; filename="{slug}.csv"'
            return response

        if fmt in ("xlsx", "xls"):
            content = build_xlsx_bytes(table)
            response = HttpResponse(
                content,
                content_type=(
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                ),
            )
            response["Content-Disposition"] = f'attachment; filename="{slug}.xlsx"'
            return response

        if fmt == "json":
            content = build_json_bytes(table)
            response = HttpResponse(content, content_type="application/json")
            response["Content-Disposition"] = f'attachment; filename="{slug}.json"'
            return response

        if fmt in ("spss_labels", "spss", "labels"):
            content = build_spss_labels_bytes(table)
            response = HttpResponse(content, content_type="text/csv; charset=utf-8")
            response["Content-Disposition"] = (
                f'attachment; filename="{slug}_spss_labels.csv"'
            )
            return response

        return Response(
            {
                "detail": "Unsupported format. Use xlsx, csv, geojson, json, or spss_labels."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class WebDataDetailView(APIView):
    """Reuses the existing detail selector, but maps it clearly in the web namespace."""

    permission_classes = [IsAuthenticated]

    def get(self, request, form_id, row_id):
        raise_if_missing(
            get_form_by_id_selector(form_id, user=request.user),
            "Form not found.",
        )
        from apps.submissions.models import SubmissionIndex

        try:
            sub_index = SubmissionIndex.objects.get(
                form_id=form_id, physical_row_id=row_id
            )
            details = raise_if_missing(
                get_submission_details_selector(str(sub_index.id)),
                "Submission not found.",
            )
            meta_serializer = SubmissionIndexSerializer(details["metadata"])
            return Response(
                {
                    "metadata": meta_serializer.data,
                    "answers": details["answers"],
                }
            )
        except SubmissionIndex.DoesNotExist:
            return Response({"detail": "Submission not found."}, status=404)

    def delete(self, request, form_id, row_id):
        form = raise_if_missing(
            get_form_by_id_selector(form_id, user=request.user),
            "Form not found.",
        )
        try:
            delete_web_row_service(form, int(row_id))
        except LookupError:
            return Response({"detail": "Submission not found."}, status=404)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(status=status.HTTP_204_NO_CONTENT)
