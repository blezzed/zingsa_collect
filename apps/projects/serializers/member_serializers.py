from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.projects.models.member import ProjectMember
from apps.projects.privileges import (
    PRIVILEGE_KEYS,
    normalize_overrides,
    normalize_role_privileges,
    effective_privileges_for_user,
)

User = get_user_model()


class ProjectMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    privilege_overrides = serializers.SerializerMethodField()
    effective_privileges = serializers.SerializerMethodField()

    class Meta:
        model = ProjectMember
        fields = [
            'id', 'user_id', 'username', 'first_name', 'last_name', 'role',
            'privilege_overrides', 'effective_privileges', 'created_at',
        ]
        read_only_fields = ['id', 'user_id', 'created_at']

    def get_privilege_overrides(self, obj):
        return normalize_overrides(obj.privilege_overrides)

    def get_effective_privileges(self, obj):
        return effective_privileges_for_user(obj.user, obj.project)


class ProjectMemberCreateSerializer(serializers.Serializer):
    username = serializers.CharField()
    role = serializers.ChoiceField(choices=ProjectMember.ROLE_CHOICES, default='collector')
    privilege_overrides = serializers.DictField(required=False, child=serializers.BooleanField())

    def validate_username(self, value):
        if not User.objects.filter(username=value).exists():
            raise serializers.ValidationError("User with this username does not exist.")
        return value

    def validate_privilege_overrides(self, value):
        return normalize_overrides(value)


class ProjectMemberUpdateSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=ProjectMember.ROLE_CHOICES, required=False)
    privilege_overrides = serializers.DictField(
        required=False,
        child=serializers.BooleanField(),
        allow_null=True,
    )

    def validate(self, attrs):
        if 'role' not in attrs and 'privilege_overrides' not in attrs:
            raise serializers.ValidationError(
                "Provide role and/or privilege_overrides."
            )
        return attrs

    def validate_privilege_overrides(self, value):
        if value is None:
            return {}
        return normalize_overrides(value)


class ProjectRolePrivilegesSerializer(serializers.Serializer):
    manager = serializers.ListField(
        child=serializers.ChoiceField(choices=PRIVILEGE_KEYS),
        required=False,
    )
    collector = serializers.ListField(
        child=serializers.ChoiceField(choices=PRIVILEGE_KEYS),
        required=False,
    )
    viewer = serializers.ListField(
        child=serializers.ChoiceField(choices=PRIVILEGE_KEYS),
        required=False,
    )

    def validate(self, attrs):
        from apps.projects.privileges import PROJECT_ROLES

        current = normalize_role_privileges(self.context.get('current'))
        for role in PROJECT_ROLES:
            if role in attrs:
                current[role] = attrs[role]
        return current
