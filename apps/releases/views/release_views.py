import hashlib
import os

from django.conf import settings
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsDeveloper
from apps.releases.models import AppRelease
from apps.releases.serializers.release_serializers import AppReleaseSerializer
from common.exceptions import ValidationFailed
from common.view_helpers import raise_if_missing


APK_MAX_BYTES = int(
    getattr(settings, "APK_MAX_BYTES", 200 * 1024 * 1024) or (200 * 1024 * 1024)
)


def _latest_id(queryset):
    latest = queryset.filter(is_published=True).order_by(
        "-version_code", "-created_at"
    ).first()
    return str(latest.id) if latest else None


def _sha256(uploaded) -> str:
    digest = hashlib.sha256()
    for chunk in uploaded.chunks():
        digest.update(chunk)
    uploaded.seek(0)
    return digest.hexdigest()


class ReleaseListCreateView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsDeveloper()]
        return [AllowAny()]

    def get(self, request):
        queryset = AppRelease.objects.select_related("uploaded_by")
        developer = bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "is_developer", lambda: False)()
        )
        if not developer:
            queryset = queryset.filter(is_published=True)
        latest_id = _latest_id(queryset)
        serializer = AppReleaseSerializer(
            queryset,
            many=True,
            context={"request": request, "latest_id": latest_id},
        )
        return Response(serializer.data)

    def post(self, request):
        uploaded = request.FILES.get("file")
        if not uploaded:
            raise ValidationFailed(
                message="Upload an APK file.",
                errors={"file": ["Choose an .apk file."]},
            )

        name = (uploaded.name or "").strip()
        ext = os.path.splitext(name)[1].lower()
        if ext != ".apk":
            raise ValidationFailed(
                message="Only Android APK files are accepted.",
                errors={"file": ["File must end with .apk."]},
            )

        size = int(getattr(uploaded, "size", 0) or 0)
        if size <= 0:
            raise ValidationFailed(
                message="The APK file is empty.",
                errors={"file": ["The APK file is empty."]},
            )
        if size > APK_MAX_BYTES:
            mb = APK_MAX_BYTES // (1024 * 1024)
            raise ValidationFailed(
                message=f"APK is larger than {mb} MB.",
                errors={"file": [f"Maximum size is {mb} MB."]},
            )

        version_name = str(request.data.get("version_name") or "").strip()
        if not version_name:
            raise ValidationFailed(
                message="Enter a version name.",
                errors={"version_name": ["Enter a version name such as 1.0.0."]},
            )

        raw_code = str(request.data.get("version_code") or "").strip()
        try:
            version_code = int(raw_code)
        except (TypeError, ValueError):
            version_code = 0
        if version_code < 1:
            raise ValidationFailed(
                message="Enter a version code.",
                errors={
                    "version_code": [
                        "Enter a positive integer (Android versionCode)."
                    ]
                },
            )

        platform = AppRelease.Platform.ANDROID
        if AppRelease.objects.filter(
            platform=platform, version_code=version_code
        ).exists():
            raise ValidationFailed(
                message="That version code is already published.",
                errors={"version_code": ["This version code already exists."]},
            )
        if AppRelease.objects.filter(
            platform=platform, version_name__iexact=version_name
        ).exists():
            raise ValidationFailed(
                message="That version name is already published.",
                errors={"version_name": ["This version name already exists."]},
            )

        notes = str(request.data.get("notes") or "").strip()
        checksum = _sha256(uploaded)
        release = AppRelease(
            platform=platform,
            version_name=version_name,
            version_code=version_code,
            notes=notes,
            file=uploaded,
            original_name=name,
            file_size=size,
            checksum=checksum,
            is_published=True,
            uploaded_by=request.user,
        )
        release.save()
        latest_id = _latest_id(AppRelease.objects.all())
        serializer = AppReleaseSerializer(
            release,
            context={"request": request, "latest_id": latest_id},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ReleaseLatestView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = AppRelease.objects.filter(
            is_published=True, platform=AppRelease.Platform.ANDROID
        ).select_related("uploaded_by")
        latest = queryset.order_by("-version_code", "-created_at").first()
        if latest is None:
            return Response({"detail": "No Android release yet."}, status=404)
        serializer = AppReleaseSerializer(
            latest,
            context={"request": request, "latest_id": str(latest.id)},
        )
        return Response(serializer.data)


class ReleaseDetailView(APIView):
    permission_classes = [IsAuthenticated, IsDeveloper]

    def delete(self, request, pk):
        release = raise_if_missing(
            AppRelease.objects.filter(pk=pk).first(),
            "Release not found.",
        )
        if release.file:
            release.file.delete(save=False)
        release.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
