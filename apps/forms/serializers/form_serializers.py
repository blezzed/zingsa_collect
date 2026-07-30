from rest_framework import serializers
from apps.forms.models import Form, FormVersion
from apps.forms.services.form_services import get_latest_published_version


class FormVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormVersion
        fields = [
            'id', 'version_number', 'version_label', 'schema',
            'checksum', 'is_published', 'physical_table_name',
            'column_mapping', 'published_at', 'created_at'
        ]
        read_only_fields = fields


class FormSerializer(serializers.ModelSerializer):
    current_version_details = serializers.SerializerMethodField()
    schema = serializers.JSONField(write_only=True, required=False)
    submission_count = serializers.SerializerMethodField()

    class Meta:
        model = Form
        fields = [
            'id', 'project', 'title', 'slug', 'description', 'mode',
            'geometry_type', 'has_geodata', 'current_version', 'current_version_details',
            'status', 'submission_table_name', 'submission_count', 'schema', 'created_by',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'project', 'slug', 'current_version', 'status',
            'submission_table_name', 'submission_count', 'created_by', 'created_at',
            'updated_at',
        ]

    def get_current_version_details(self, obj):
        """
        Builder uses the working current_version.
        Collector/available endpoints can request published_only so devices never
        receive an unpublished draft tip.
        """
        if self.context.get("published_only"):
            version = get_latest_published_version(obj)
        else:
            version = obj.current_version
        if not version:
            return None
        return FormVersionSerializer(version).data

    def get_submission_count(self, obj) -> int:
        annotated = getattr(obj, 'submission_count', None)
        if annotated is not None:
            return int(annotated)
        return obj.submissions.count()
