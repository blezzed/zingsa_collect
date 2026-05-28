from rest_framework import serializers
from apps.forms.models import Form, FormVersion

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
    current_version_details = FormVersionSerializer(source='current_version', read_only=True)
    schema = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = Form
        fields = [
            'id', 'project', 'title', 'slug', 'description', 'mode', 
            'geometry_type', 'has_geodata', 'current_version', 'current_version_details', 
            'status', 'submission_table_name', 'schema', 'created_by', 
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'project', 'slug', 'current_version', 'status', 
            'submission_table_name', 'created_by', 'created_at', 'updated_at'
        ]
