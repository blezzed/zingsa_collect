from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import CanManageStaff, CanManageUsers
from apps.accounts.serializers.user_serializers import (
    EndUserAdminSerializer,
    EndUserAdminUpdateSerializer,
    StaffCreateSerializer,
    StaffUpdateSerializer,
    StaffUserSerializer,
)
from apps.accounts.services.staff_services import (
    create_staff_user,
    list_end_users,
    list_staff_users,
    set_end_user_active,
    update_staff_user,
)
from common.exceptions import ValidationFailed

User = get_user_model()


class StaffListCreateView(APIView):
    """
    GET/POST /api/accounts/staff/
    Admin+ only.
    """

    permission_classes = [CanManageStaff]

    def get(self, request):
        items = list_staff_users()
        return Response(StaffUserSerializer(items, many=True).data)

    def post(self, request):
        serializer = StaffCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = create_staff_user(
            actor=request.user,
            username=data["username"],
            password=data["password"],
            staff_role=data["staff_role"],
            email=data.get("email") or "",
            first_name=data.get("first_name") or "",
            last_name=data.get("last_name") or "",
        )
        return Response(
            StaffUserSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class StaffDetailView(APIView):
    """
    PATCH /api/accounts/staff/<id>/
    Admin+ only.
    """

    permission_classes = [CanManageStaff]

    def patch(self, request, user_id: int):
        try:
            target = User.objects.get(pk=user_id)
        except User.DoesNotExist as exc:
            raise ValidationFailed(message="Staff user not found.") from exc

        serializer = StaffUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = update_staff_user(actor=request.user, user=target, **serializer.validated_data)
        return Response(StaffUserSerializer(user).data)


class EndUserAdminListView(APIView):
    """
    GET /api/accounts/users-admin/
    Manager+ only. End users (non-staff).
    """

    permission_classes = [CanManageUsers]

    def get(self, request):
        search = request.query_params.get("q") or ""
        items = list_end_users(search=search)
        return Response(EndUserAdminSerializer(items, many=True).data)


class EndUserAdminDetailView(APIView):
    """
    PATCH /api/accounts/users-admin/<id>/
    Manager+ — activate / deactivate end users.
    """

    permission_classes = [CanManageUsers]

    def patch(self, request, user_id: int):
        try:
            target = User.objects.get(pk=user_id)
        except User.DoesNotExist as exc:
            raise ValidationFailed(message="User not found.") from exc

        serializer = EndUserAdminUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = set_end_user_active(
            actor=request.user,
            user=target,
            is_active=serializer.validated_data["is_active"],
        )
        return Response(EndUserAdminSerializer(user).data)
