from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.organizations.models.member import OrganizationMember

User = get_user_model()

class OrganizationMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = OrganizationMember
        fields = ['id', 'user_id', 'username', 'first_name', 'last_name', 'role', 'created_at']
        read_only_fields = ['id', 'user_id', 'created_at']


class OrganizationMemberCreateSerializer(serializers.Serializer):
    username = serializers.CharField()
    role = serializers.ChoiceField(choices=OrganizationMember.ROLE_CHOICES, default='member')

    def validate_username(self, value):
        if not User.objects.filter(username=value).exists():
            raise serializers.ValidationError("User with this username does not exist.")
        return value
