from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

User = get_user_model()

# Djoser's default UserSerializer only exposes id/login/REQUIRED_FIELDS
# (usually email) — first_name / last_name are omitted unless added here.
PROFILE_FIELDS = (
    "first_name",
    "last_name",
    "country",
    "city",
    "sector",
    "organization_type",
    "bio",
    "social_linkedin",
    "newsletter_opt_in",
)


class UserSuggestSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class CollectUserSerializer(DjoserUserSerializer):
    """Current-user serializer with Collect profile fields."""

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = tuple(
            dict.fromkeys(
                tuple(DjoserUserSerializer.Meta.fields) + PROFILE_FIELDS
            )
        )
        read_only_fields = tuple(
            f
            for f in (
                getattr(DjoserUserSerializer.Meta, "read_only_fields", ()) or ()
            )
            if f not in ("first_name", "last_name", "email")
        )
