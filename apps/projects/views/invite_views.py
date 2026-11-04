from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from apps.projects.permissions import HasProjectPrivilege
from apps.projects.selectors.invite_selectors import (
    get_project_invite_selector,
    get_project_invites_selector,
)
from apps.projects.selectors.project_selectors import get_project_by_id_selector
from apps.projects.serializers.invite_serializers import (
    InviteCodeSerializer,
    ProjectInviteCreateSerializer,
    ProjectInviteCreatedSerializer,
    ProjectInviteSerializer,
)
from apps.projects.services.invite_services import (
    INVALID_INVITE_DETAIL,
    cancel_project_invite_service,
    create_project_invite_service,
    join_project_invite_service,
    verify_project_invite_service,
)
from common.view_helpers import raise_if_missing


class InviteCodeIPThrottle(SimpleRateThrottle):
    """
    Shared per-IP limit for verify and join.
    Uses Django's default cache (the same alias DRF throttling already uses).
    """

    scope = 'invite_code'

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        if not ident:
            return None
        return self.cache_format % {'scope': self.scope, 'ident': ident}


def _invalid_invite_response() -> Response:
    return Response(
        {'detail': INVALID_INVITE_DETAIL},
        status=status.HTTP_400_BAD_REQUEST,
    )


class ProjectInviteListCreateView(APIView):
    def get_permissions(self):
        return [IsAuthenticated(), HasProjectPrivilege('manage_members')]

    def get(self, request, project_id):
        project = raise_if_missing(
            get_project_by_id_selector(project_id, user=request.user),
            'Project not found.',
        )
        invites = get_project_invites_selector(project)
        return Response(ProjectInviteSerializer(invites, many=True).data)

    def post(self, request, project_id):
        project = raise_if_missing(
            get_project_by_id_selector(project_id, user=request.user),
            'Project not found.',
        )
        serializer = ProjectInviteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        invite, plain_code = create_project_invite_service(
            project=project,
            created_by=request.user,
            max_uses=data['max_uses'],
            expires_at=data.get('expires_at'),
            label=data.get('label', ''),
        )
        payload = ProjectInviteCreatedSerializer(
            invite,
            context={'plain_code': plain_code},
        )
        return Response(payload.data, status=status.HTTP_201_CREATED)


class ProjectInviteCancelView(APIView):
    permission_classes = [IsAuthenticated, HasProjectPrivilege]
    required_privilege = 'manage_members'

    def post(self, request, project_id, invite_id):
        project = raise_if_missing(
            get_project_by_id_selector(project_id, user=request.user),
            'Project not found.',
        )
        invite = raise_if_missing(
            get_project_invite_selector(project, invite_id),
            'Invite not found.',
        )
        invite = cancel_project_invite_service(invite)
        return Response(ProjectInviteSerializer(invite).data)


class InviteVerifyView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [InviteCodeIPThrottle]

    def post(self, request, token):
        serializer = InviteCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = verify_project_invite_service(
            token=token,
            code=serializer.validated_data['code'],
        )
        if result is None:
            return _invalid_invite_response()
        return Response(result)


class InviteJoinView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [InviteCodeIPThrottle]

    def post(self, request, token):
        serializer = InviteCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = join_project_invite_service(
            token=token,
            code=serializer.validated_data['code'],
            user=request.user,
        )
        if result is None:
            return _invalid_invite_response()
        return Response(result)
