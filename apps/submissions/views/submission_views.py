from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.forms.selectors.form_selectors import get_form_by_id_selector
from apps.submissions.selectors.submission_selectors import (
    get_submissions_by_form_selector,
    get_submission_details_selector,
)
from apps.submissions.serializers.submission_serializers import SubmissionIndexSerializer
from common.view_helpers import raise_if_missing


class FormSubmissionsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, form_id):
        form = raise_if_missing(
            get_form_by_id_selector(form_id, user=request.user),
            'Form not found.',
        )
        answers = get_submissions_by_form_selector(form)
        return Response(answers)


class SubmissionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        details = raise_if_missing(
            get_submission_details_selector(str(pk)),
            'Submission not found.',
        )
        meta_serializer = SubmissionIndexSerializer(details['metadata'])
        return Response({
            'metadata': meta_serializer.data,
            'answers': details['answers'],
        })
