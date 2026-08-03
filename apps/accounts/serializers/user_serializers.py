from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer
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
    "is_superuser",
    "is_staff",
    "staff_role",
)

CREATE_PROFILE_FIELDS = (
    "first_name",
    "last_name",
    "country",
    "sector",
    "organization_type",
    "newsletter_opt_in",
)


def user_capability_payload(user) -> dict:
    role = user.effective_staff_role()
    label = ""
    if role is not None:
        label = dict(User.StaffRole.choices).get(role, "")
    return {
        "staff_role": role,
        "staff_role_label": label,
        **user.staff_capabilities(),
    }


class UserSuggestSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class CollectUserCreateSerializer(DjoserUserCreateSerializer):
    """Djoser user create with Collect profile fields at signup."""

    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = tuple(
            dict.fromkeys(
                tuple(DjoserUserCreateSerializer.Meta.fields) + CREATE_PROFILE_FIELDS
            )
        )


class CollectUserSerializer(DjoserUserSerializer):
    """Current-user serializer with Collect profile fields."""

    staff_role_label = serializers.SerializerMethodField()
    is_platform_staff = serializers.SerializerMethodField()
    is_developer = serializers.SerializerMethodField()
    can_manage_staff = serializers.SerializerMethodField()
    can_manage_users = serializers.SerializerMethodField()
    can_view_system_overview = serializers.SerializerMethodField()
    can_view_all_feedback = serializers.SerializerMethodField()
    can_view_storage = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = tuple(
            dict.fromkeys(
                tuple(DjoserUserSerializer.Meta.fields)
                + PROFILE_FIELDS
                + (
                    "staff_role_label",
                    "is_platform_staff",
                    "is_developer",
                    "can_manage_staff",
                    "can_manage_users",
                    "can_view_system_overview",
                    "can_view_all_feedback",
                    "can_view_storage",
                )
            )
        )
        read_only_fields = tuple(
            dict.fromkeys(
                [
                    *(
                        f
                        for f in (
                            getattr(DjoserUserSerializer.Meta, "read_only_fields", ())
                            or ()
                        )
                        if f not in ("first_name", "last_name", "email")
                    ),
                    "is_superuser",
                    "is_staff",
                    "staff_role",
                    "staff_role_label",
                    "is_platform_staff",
                    "is_developer",
                    "can_manage_staff",
                    "can_manage_users",
                    "can_view_system_overview",
                    "can_view_all_feedback",
                    "can_view_storage",
                ]
            )
        )

    def get_staff_role_label(self, obj):
        role = obj.effective_staff_role()
        if role is None:
            return ""
        return dict(User.StaffRole.choices).get(role, "")

    def get_is_platform_staff(self, obj):
        return obj.is_platform_staff()

    def get_is_developer(self, obj):
        return obj.is_developer()

    def get_can_manage_staff(self, obj):
        return obj.can_manage_staff()

    def get_can_manage_users(self, obj):
        return obj.can_manage_users()

    def get_can_view_system_overview(self, obj):
        return obj.can_view_system_overview()

    def get_can_view_all_feedback(self, obj):
        return obj.can_view_all_feedback()

    def get_can_view_storage(self, obj):
        return obj.can_view_storage()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Expose effective role (Developer for superusers without staff_role set).
        data["staff_role"] = instance.effective_staff_role()
        return data


class StaffUserSerializer(serializers.ModelSerializer):
    staff_role_label = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "staff_role",
            "staff_role_label",
            "date_joined",
            "last_login",
        ]
        read_only_fields = [
            "id",
            "staff_role_label",
            "date_joined",
            "last_login",
            "is_staff",
        ]

    def get_staff_role_label(self, obj):
        if obj.staff_role is None:
            return ""
        return dict(User.StaffRole.choices).get(obj.staff_role, "")


class StaffCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(required=False, allow_blank=True, default="")
    last_name = serializers.CharField(required=False, allow_blank=True, default="")
    staff_role = serializers.ChoiceField(choices=User.StaffRole.choices)


class StaffUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
    staff_role = serializers.ChoiceField(
        choices=User.StaffRole.choices, required=False
    )
    password = serializers.CharField(
        write_only=True, required=False, allow_blank=True, min_length=8
    )


class EndUserAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "date_joined",
            "last_login",
            "country",
            "sector",
        ]
        read_only_fields = fields


class EndUserAdminUpdateSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()
