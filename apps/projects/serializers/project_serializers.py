from rest_framework import serializers
from django.db.models.functions import Lower

from apps.projects.models import Project
from apps.projects.privileges import (
    normalize_role_privileges,
    effective_privileges_for_user,
)


class ProjectSerializer(serializers.ModelSerializer):
    owner_username = serializers.ReadOnlyField(source='owner.username')
    organization_name = serializers.ReadOnlyField(source='organization.name')
    role_privileges = serializers.SerializerMethodField()
    my_privileges = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'code', 'description', 'organization',
            'organization_name', 'owner', 'owner_username', 'status',
            'role_privileges', 'my_privileges',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'code', 'owner', 'role_privileges', 'my_privileges',
            'created_at', 'updated_at'
        ]

    def validate_name(self, value: str) -> str:
        name = (value or "").strip()
        if not name:
            raise serializers.ValidationError("Enter a project name.")
        qs = Project.objects.annotate(name_ci=Lower("name")).filter(name_ci=name.lower())
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "A project with this name already exists."
            )
        return name

    def get_role_privileges(self, obj):
        return normalize_role_privileges(obj.role_privileges)

    def get_my_privileges(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        return effective_privileges_for_user(user, obj)
