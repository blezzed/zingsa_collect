from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

from apps.mediafiles.models import MediaFile
from apps.mediafiles.serializers.media_serializers import MediaFileSerializer
from common.exceptions import ValidationFailed


class MediaUploadView(APIView):
    """
    Handles file uploads from the mobile client.
    Expects multipart/form-data with a 'file' key.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            raise ValidationFailed(
                message="No file uploaded.",
                errors={
                    'file': [
                        "No file uploaded. Ensure 'file' key is present in multipart/form-data.",
                    ],
                },
            )

        media_file = MediaFile(
            file=uploaded_file,
            original_name=uploaded_file.name,
            file_type=uploaded_file.content_type,
            file_size=uploaded_file.size,
            uploaded_by=request.user,
        )
        media_file.save()

        serializer = MediaFileSerializer(media_file, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
