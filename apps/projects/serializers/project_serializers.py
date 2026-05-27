from rest_framework import serializers
from apps.projects.models import Project

class ProjectSerializer(serializers.ModelSerializer):
    owner_username = serializers.ReadOnlyField(source='owner.username')
    organization_name = serializers.ReadOnlyField(source='organization.name')

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'code', 'description', 'organization', 
            'organization_name', 'owner', 'owner_username', 'status', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'code', 'owner', 'created_at', 'updated_at']
