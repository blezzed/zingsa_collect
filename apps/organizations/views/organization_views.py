from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.organizations.models import Organization
from apps.organizations.serializers.organization_serializers import OrganizationSerializer
from apps.organizations.services.organization_services import create_organization_service
from common.exceptions import ResourceNotFound
from common.permissions import IsOrganizationAdmin
from common.view_helpers import require_non_empty_string


class OrganizationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orgs = Organization.objects.filter(members__user=request.user).distinct()
        serializer = OrganizationSerializer(orgs, many=True)
        return Response(serializer.data)

    def post(self, request):
        name = require_non_empty_string(request.data, 'name', label='Organization name')
        org = create_organization_service(
            name=name,
            description=request.data.get('description'),
            contact_email=request.data.get('contact_email'),
            phone_number=request.data.get('phone_number'),
            address=request.data.get('address'),
            user=request.user,
        )
        return Response(OrganizationSerializer(org).data, status=status.HTTP_201_CREATED)


class OrganizationDetailView(APIView):
    permission_classes = [IsAuthenticated, IsOrganizationAdmin]

    def _get_org(self, org_id):
        try:
            return Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            raise ResourceNotFound('Organization not found.')

    def get(self, request, org_id):
        org = self._get_org(org_id)
        self.check_object_permissions(request, org)
        return Response(OrganizationSerializer(org).data)

    def patch(self, request, org_id):
        org = self._get_org(org_id)
        self.check_object_permissions(request, org)

        serializer = OrganizationSerializer(org, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        for attr, value in serializer.validated_data.items():
            setattr(org, attr, value)
        org.full_clean()
        org.save()

        return Response(OrganizationSerializer(org).data)

    def delete(self, request, org_id):
        org = self._get_org(org_id)
        self.check_object_permissions(request, org)
        org.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
