from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.feedback.filters import FeedbackFilter
from apps.feedback.models import Feedback
from apps.feedback.serializers.feedback_serializers import FeedbackSerializer
from apps.feedback.services.feedback_services import (
    create_feedback_service,
    list_feedback_for_user,
)
from common.view_helpers import require_non_empty_string


class FeedbackPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class FeedbackListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = FeedbackPagination

    def get(self, request):
        queryset = list_feedback_for_user(request.user)
        filtered = FeedbackFilter(request.query_params, queryset=queryset).qs
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(filtered, request, view=self)
        serializer = FeedbackSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        subject = require_non_empty_string(
            request.data, "subject", label="Subject"
        )
        message = require_non_empty_string(
            request.data, "message", label="Message"
        )
        category = (
            request.data.get("category") or Feedback.Category.IMPROVEMENT
        ).strip()
        valid = {c.value for c in Feedback.Category}
        if category not in valid:
            category = Feedback.Category.IMPROVEMENT

        page_url = request.data.get("page_url") or ""
        if page_url is not None:
            page_url = str(page_url).strip()

        item = create_feedback_service(
            user=request.user,
            subject=subject,
            message=message,
            category=category,
            page_url=page_url,
        )
        return Response(
            FeedbackSerializer(item).data,
            status=status.HTTP_201_CREATED,
        )
