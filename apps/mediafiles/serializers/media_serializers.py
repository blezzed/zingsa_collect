from rest_framework import serializers
from apps.mediafiles.models import MediaFile
from common.media_url_rewrite import rewrite_public_media_url

class MediaFileSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = MediaFile
        fields = ['id', 'url', 'original_name', 'file_type', 'file_size', 'created_at']

    def get_url(self, obj):
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url'):
            url = rewrite_public_media_url(obj.file.url)
            # Relative /minio/... → absolute for the current Host (LAN or public IP).
            if url.startswith('/') and request is not None:
                return request.build_absolute_uri(url)
            if not (url.startswith('http://') or url.startswith('https://')):
                if request is not None:
                    return request.build_absolute_uri(url)
            return url
        return None
