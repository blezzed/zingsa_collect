from rest_framework import serializers

from apps.feedback.models import Feedback


class FeedbackSerializer(serializers.ModelSerializer):
    category_label = serializers.CharField(
        source="get_category_display", read_only=True
    )
    status_label = serializers.CharField(
        source="get_status_display", read_only=True
    )
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)
    resolved_by_username = serializers.SerializerMethodField()

    class Meta:
        model = Feedback
        fields = [
            "id",
            "user_id",
            "username",
            "user_email",
            "category",
            "category_label",
            "status",
            "status_label",
            "subject",
            "message",
            "page_url",
            "status_note",
            "resolved_at",
            "resolved_by_username",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user_id",
            "username",
            "user_email",
            "category_label",
            "status",
            "status_label",
            "status_note",
            "resolved_at",
            "resolved_by_username",
            "created_at",
            "updated_at",
        ]

    def get_resolved_by_username(self, obj):
        resolved_by = getattr(obj, "resolved_by", None)
        return resolved_by.username if resolved_by else None
