from rest_framework import serializers
from django.db.models.functions import Lower

from apps.projects.models import Project
from apps.projects.privileges import (
    normalize_role_privileges,
    effective_privileges_for_user,
)
from apps.projects.services.project_contact import (
    PROJECT_CONTACT_FIELDS,
    contact_suggestion_for_owner,
    normalize_project_contact,
)


class ProjectSerializer(serializers.ModelSerializer):
    owner_username = serializers.ReadOnlyField(source='owner.username')
    organization_name = serializers.ReadOnlyField(source='organization.name')
    role_privileges = serializers.SerializerMethodField()
    my_privileges = serializers.SerializerMethodField()
    submission_count = serializers.SerializerMethodField()
    submission_bytes = serializers.SerializerMethodField()
    contact_name = serializers.CharField(
        max_length=150, required=False, allow_blank=True, allow_null=True
    )
    contact_phone = serializers.CharField(
        max_length=30, required=False, allow_blank=True, allow_null=True
    )
    contact_email = serializers.CharField(
        max_length=254, required=False, allow_blank=True, allow_null=True
    )
    contact_note = serializers.CharField(
        max_length=300, required=False, allow_blank=True, allow_null=True
    )
    contact_suggestion = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'code', 'description', 'organization',
            'organization_name', 'owner', 'owner_username', 'status',
            'contact_name', 'contact_phone', 'contact_email', 'contact_note',
            'contact_suggestion',
            'role_privileges', 'my_privileges',
            'submission_count', 'submission_bytes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'code', 'owner', 'contact_suggestion',
            'role_privileges', 'my_privileges',
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

    def to_internal_value(self, data):
        # Contact is saved only by the project update endpoint. A new project
        # stays blank even if the client sends the owner's details.
        if self.instance is None and isinstance(data, dict):
            data = {
                key: value
                for key, value in data.items()
                if key not in PROJECT_CONTACT_FIELDS
            }
        return super().to_internal_value(data)

    def validate(self, attrs):
        if self.instance is None or not any(
            field in attrs for field in PROJECT_CONTACT_FIELDS
        ):
            return attrs
        merged = {}
        for field in PROJECT_CONTACT_FIELDS:
            if field in attrs:
                merged[field] = attrs[field]
            else:
                merged[field] = getattr(self.instance, field, "") or ""
        normalized = normalize_project_contact(merged)
        for field in PROJECT_CONTACT_FIELDS:
            if field in attrs:
                attrs[field] = normalized[field]
        return attrs

    def get_contact_suggestion(self, obj):
        if "manage_members" not in self._effective_privileges(obj):
            return None
        owner = getattr(obj, "owner", None)
        if owner is None:
            return None
        return contact_suggestion_for_owner(owner)

    def get_role_privileges(self, obj):
        return normalize_role_privileges(obj.role_privileges)

    def _effective_privileges(self, obj):
        cache = self.context.setdefault("_effective_privileges", {})
        key = obj.pk
        if key not in cache:
            request = self.context.get("request")
            user = getattr(request, "user", None)
            cache[key] = effective_privileges_for_user(user, obj)
        return cache[key]

    def get_my_privileges(self, obj):
        return self._effective_privileges(obj)

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
