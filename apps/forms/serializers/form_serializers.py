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
    submission_bytes = serializers.SerializerMethodField()
    published_version_number = serializers.SerializerMethodField()
    published_checksum = serializers.SerializerMethodField()
    force_update = serializers.SerializerMethodField()

    class Meta:
        model = Form
        fields = [
            'id', 'project', 'title', 'slug', 'description', 'mode',
            'geometry_type', 'has_geodata', 'current_version', 'current_version_details',
            'published_version_number', 'published_checksum', 'force_update',
            'status', 'submission_table_name', 'submission_count', 'submission_bytes',
            'schema', 'created_by',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'project', 'slug', 'current_version', 'status',
            'submission_table_name', 'submission_count', 'submission_bytes',
            'created_by', 'created_at',
            'updated_at', 'published_version_number', 'published_checksum', 'force_update',
        ]

    def _published_tip(self, obj):
        if self.context.get("published_only"):
            return get_latest_published_version(obj)
        return obj.current_version

    def get_current_version_details(self, obj):
        """
        Builder uses the working current_version.
        Collector/available endpoints can request published_only so devices never
        receive an unpublished draft tip.
        """
        version = self._published_tip(obj)
        if not version:
            return None
        return FormVersionSerializer(version).data

    def get_published_version_number(self, obj):
        if not self.context.get("published_only"):
            return None
        version = get_latest_published_version(obj)
        return version.version_number if version else None

    def get_published_checksum(self, obj):
        if not self.context.get("published_only"):
            return None
        version = get_latest_published_version(obj)
        return version.checksum if version else None

    def get_force_update(self, obj):
        """
        Collector signal: local definitions with a lower version_number / different
        checksum must be replaced with the published tip from download.
        """
        if not self.context.get("published_only"):
            return False
        return get_latest_published_version(obj) is not None

    def get_submission_count(self, obj) -> int:
        annotated = getattr(obj, 'submission_count', None)
        if annotated is not None:
            return int(annotated)
        return obj.submissions.count()

    def get_submission_bytes(self, obj) -> int:
        annotated = getattr(obj, 'submission_bytes', None)
        if annotated is not None:
            return int(annotated)
        from django.db.models import Sum
        from apps.submissions.models import SubmissionMedia

        total = SubmissionMedia.objects.filter(
            submission_index__form_id=obj.id
        ).aggregate(total=Sum("size"))["total"]
        return int(total or 0)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # When serving collectors, never expose a draft tip id as current_version.
        if self.context.get("published_only"):
            version = get_latest_published_version(instance)
            data["current_version"] = str(version.id) if version else None
        return data
