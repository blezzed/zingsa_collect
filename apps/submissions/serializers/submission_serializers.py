from rest_framework import serializers
from apps.submissions.models import SubmissionIndex, SubmissionMedia

class SubmissionMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubmissionMedia
        fields = [
            'id', 'field_id', 'file', 'file_url', 'file_type', 
            'original_name', 'mime_type', 'size', 'checksum', 'created_at'
        ]


class SubmissionIndexSerializer(serializers.ModelSerializer):
    submitted_by_username = serializers.ReadOnlyField(source='submitted_by.username')
    media_files = SubmissionMediaSerializer(many=True, read_only=True)

    class Meta:
        model = SubmissionIndex
        fields = [
            'id', 'project', 'form', 'form_version', 'submitted_by', 
            'submitted_by_username', 'device_id', 'client_submission_id', 
            'physical_table_name', 'physical_row_id', 'sync_status', 
            'synced_at', 'created_at', 'updated_at', 'media_files'
        ]
        read_only_fields = fields
