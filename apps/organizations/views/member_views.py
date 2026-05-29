from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from common.permissions import IsOrganizationAdmin
from common.exceptions import ResourceNotFound
from apps.organizations.models import Organization
from apps.organizations.models.member import OrganizationMember
from apps.organizations.serializers.member_serializers import (
    OrganizationMemberSerializer,
    OrganizationMemberCreateSerializer
)
from apps.organizations.services.member_services import (
    add_org_member_service,
    update_org_member_service,
    remove_org_member_service
)

class OrganizationMemberListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsOrganizationAdmin]

    def _get_org(self, request, org_id):
        try:
            org = Organization.objects.get(id=org_id)
            self.check_object_permissions(request, org)
            return org
        except Organization.DoesNotExist:
            raise ResourceNotFound('Organization not found.')

    def get(self, request, org_id):
        org = self._get_org(request, org_id)
        members = OrganizationMember.objects.filter(organization=org)
        serializer = OrganizationMemberSerializer(members, many=True)
        return Response(serializer.data)

    def post(self, request, org_id):
        org = self._get_org(request, org_id)
        serializer = OrganizationMemberCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        member = add_org_member_service(
            organization=org,
            username=serializer.validated_data['username'],
            role=serializer.validated_data['role']
        )
        return Response(OrganizationMemberSerializer(member).data, status=status.HTTP_201_CREATED)


class OrganizationMemberDetailView(APIView):
    permission_classes = [IsAuthenticated, IsOrganizationAdmin]

    def _get_org(self, request, org_id):
        try:
            org = Organization.objects.get(id=org_id)
            self.check_object_permissions(request, org)
            return org
        except Organization.DoesNotExist:
            raise ResourceNotFound('Organization not found.')

    def patch(self, request, org_id, username):
        org = self._get_org(request, org_id)
        role = request.data.get('role')
        if not role:
            return Response({"role": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)
            
        member = update_org_member_service(organization=org, username=username, role=role)
        return Response(OrganizationMemberSerializer(member).data)

    def delete(self, request, org_id, username):
        org = self._get_org(request, org_id)
        remove_org_member_service(organization=org, username=username)
        return Response(status=status.HTTP_204_NO_CONTENT)

