from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from common.permissions import IsProjectCollectorOrHigher

from apps.forms.models import FormVersion
from apps.submissions.services.submission_services import sync_submission_to_physical_table_service
from apps.submissions.serializers.submission_serializers import SubmissionIndexSerializer
from apps.sync.services.sync_services import bulk_sync_submissions_service
from apps.sync.models import SyncLog
from apps.sync.serializers.sync_serializers import SyncLogSerializer
from common.exceptions import ResourceNotFound, ValidationFailed
from common.view_helpers import require_fields, require_non_empty_string


class SingleSubmissionSyncView(APIView):
    permission_classes = [IsAuthenticated, IsProjectCollectorOrHigher]

    def post(self, request):
        data = request.data
        require_fields(
            data,
            'device_id',
            'client_submission_id',
            'form_version_id',
        )

        try:
            form_version = FormVersion.objects.select_related('form').get(
                id=data['form_version_id'],
            )
        except FormVersion.DoesNotExist:
            raise ResourceNotFound('Form version not found.')

        sub_index, is_duplicate = sync_submission_to_physical_table_service(
            client_submission_id=data['client_submission_id'],
            device_id=data['device_id'],
            form_version=form_version,
            answers=data.get('answers', {}),
            user=request.user,
        )

        serializer = SubmissionIndexSerializer(sub_index)
        response_status = status.HTTP_200_OK if is_duplicate else status.HTTP_201_CREATED
        return Response({
            'success': True,
            'is_duplicate': is_duplicate,
            'submission': serializer.data,
        }, status=response_status)


class BulkSubmissionSyncView(APIView):
    permission_classes = [IsAuthenticated, IsProjectCollectorOrHigher]

    def post(self, request):
        data = request.data
        device_id = require_non_empty_string(data, 'device_id', label='device_id')

        submissions = data.get('submissions', [])
        if not isinstance(submissions, list):
            raise ValidationFailed(
                message='submissions must be a list.',
                errors={'submissions': ['Expected a list of submission objects.']},
            )

        project = None
        form = None
        if submissions:
            first_sub = submissions[0]
            version_id = first_sub.get('form_version_id')
            if version_id:
                try:
                    fv = FormVersion.objects.select_related('form', 'form__project').get(
                        id=version_id,
                    )
                    form = fv.form
                    project = fv.form.project
                except FormVersion.DoesNotExist:
                    raise ResourceNotFound(
                        'Form version not found for the first submission in the batch.',
                    )

        result = bulk_sync_submissions_service(
            device_id=device_id,
            submissions_list=submissions,
            project=project,
            form=form,
            user=request.user,
        )
        result['success'] = result.get('total_failed', 0) == 0
        return Response(result, status=status.HTTP_200_OK)


class SyncStatusDetailView(APIView):
    permission_classes = [IsAuthenticated, IsProjectCollectorOrHigher]

    def get(self, request, pk):
        try:
            sync_log = SyncLog.objects.get(id=pk)
        except SyncLog.DoesNotExist:
            raise ResourceNotFound('Sync log not found.')

        serializer = SyncLogSerializer(sync_log)
        return Response(serializer.data)
