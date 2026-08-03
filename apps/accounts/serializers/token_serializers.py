from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.accounts.serializers.user_serializers import user_capability_payload


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        caps = user_capability_payload(self.user)
        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "is_superuser": self.user.is_superuser,
            "is_staff": self.user.is_staff,
            **caps,
        }

        return data
