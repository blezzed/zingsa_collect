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
    submission_count = serializers.SerializerMethodField()
    submission_bytes = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'code', 'description', 'organization',
            'organization_name', 'owner', 'owner_username', 'status',
            'role_privileges', 'my_privileges',
            'submission_count', 'submission_bytes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'code', 'owner', 'role_privileges', 'my_privileges',
            'submission_count', 'submission_bytes',
            'created_at', 'updated_at'
        ]

    def validate_name(self, value: str) -> str:
        name = (value or "").strip()
        if not name:
            raise serializers.ValidationError("Enter a project name.")
        request = self.context.get("request")
        owner = getattr(self.instance, "owner", None)
        if owner is None:
            user = getattr(request, "user", None)
            if user is not None and getattr(user, "is_authenticated", False):
                owner = user
        qs = Project.objects.annotate(name_ci=Lower("name")).filter(
            name_ci=name.lower()
        )
        if owner is not None:
            qs = qs.filter(owner=owner)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "You already have a project with this name."
            )
        return name

    def get_role_privileges(self, obj):
        return normalize_role_privileges(obj.role_privileges)

    def get_my_privileges(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        return effective_privileges_for_user(user, obj)

    def get_submission_count(self, obj) -> int:
        value = getattr(obj, "submission_count", None)
        if value is not None:
            return int(value)
        return obj.submissions.count()

    def get_submission_bytes(self, obj) -> int:
        value = getattr(obj, "submission_bytes", None)
        if value is not None:
            return int(value)
        from django.db.models import Sum
        from apps.submissions.models import SubmissionMedia

        total = SubmissionMedia.objects.filter(
            submission_index__project_id=obj.id
        ).aggregate(total=Sum("size"))["total"]
        return int(total or 0)
