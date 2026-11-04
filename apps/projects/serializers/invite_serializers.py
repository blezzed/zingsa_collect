from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from apps.projects.models.invite import (
    INVITE_MAX_EXPIRY_DAYS,
    INVITE_MAX_USES,
    INVITE_MIN_USES,
    ProjectInvite,
    ProjectInviteJoin,
)


class ProjectInviteCreateSerializer(serializers.Serializer):
    max_uses = serializers.IntegerField(min_value=INVITE_MIN_USES, max_value=INVITE_MAX_USES)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    label = serializers.CharField(required=False, allow_blank=True, max_length=200)

    def validate_expires_at(self, value):
        if value is None:
            return value
        limit = timezone.now() + timedelta(days=INVITE_MAX_EXPIRY_DAYS)
        if value > limit:
            raise serializers.ValidationError(
                "Expiry can't be more than 90 days from now."
            )
        return value

    def validate_label(self, value):
        return (value or '').strip()


class InviteCodeSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=64, allow_blank=False, trim_whitespace=False)


class ProjectInviteJoinReadSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ProjectInviteJoin
        fields = ['username', 'joined_at']


class ProjectInviteSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    share_url = serializers.SerializerMethodField()
    joined = ProjectInviteJoinReadSerializer(source='joins', many=True, read_only=True)

    class Meta:
        model = ProjectInvite
        fields = [
            'id',
            'label',
            'status',
            'expires_at',
            'max_uses',
            'uses',
            'failed_attempts',
            'created_by',
            'created_at',
            'share_url',
            'joined',
        ]

    def get_status(self, obj) -> str:
        return obj.derived_status()

    def get_created_by(self, obj):
        if obj.created_by_id is None:
            return None
        return obj.created_by.username

    def get_share_url(self, obj) -> str:
        return obj.share_url


class ProjectInviteCreatedSerializer(ProjectInviteSerializer):
    """Create response only. The plain code is not on the model."""

    code = serializers.SerializerMethodField()

    class Meta(ProjectInviteSerializer.Meta):
        fields = ProjectInviteSerializer.Meta.fields + ['code']

    def get_code(self, obj) -> str:
        return self.context['plain_code']
