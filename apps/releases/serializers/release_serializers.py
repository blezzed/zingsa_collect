from rest_framework import serializers

from apps.releases.models import AppRelease
from common.media_url_rewrite import rewrite_public_media_url


class AppReleaseSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()
    uploaded_by_username = serializers.ReadOnlyField(
        source="uploaded_by.username"
    )
    is_latest = serializers.SerializerMethodField()

    class Meta:
        model = AppRelease
        fields = [
            "id",
            "platform",
            "version_name",
            "version_code",
            "notes",
            "original_name",
            "file_size",
            "checksum",
            "is_published",
            "is_latest",
            "download_url",
            "uploaded_by_username",
            "created_at",
        ]
        read_only_fields = fields

    def get_download_url(self, obj):
        request = self.context.get("request")
        if not obj.file or not hasattr(obj.file, "url"):
            return None
        url = rewrite_public_media_url(obj.file.url)
        if url.startswith("/") and request is not None:
            return request.build_absolute_uri(url)
        if not (url.startswith("http://") or url.startswith("https://")):
            if request is not None:
                return request.build_absolute_uri(url)
        return url

    def get_is_latest(self, obj) -> bool:
        latest_id = self.context.get("latest_id")
        if latest_id is not None:
            return str(obj.id) == str(latest_id)
        return False
