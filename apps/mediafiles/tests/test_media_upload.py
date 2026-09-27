from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.mediafiles.models import MediaFile

User = get_user_model()

class MediaUploadTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_authenticate(user=self.user)

    def test_upload_media_file_success(self):
        url = reverse('mediafiles:upload')
        
        # Create a dummy image file
        file_content = b"fake image data"
        uploaded_file = SimpleUploadedFile(
            name='test_photo.jpg',
            content=file_content,
            content_type='image/jpeg'
        )

        response = self.client.post(url, {'file': uploaded_file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertIn('url', response.data)
        self.assertEqual(response.data['original_name'], 'test_photo.jpg')
        self.assertEqual(response.data['file_type'], 'image/jpeg')
        self.assertEqual(response.data['file_size'], len(file_content))
        
        # Verify in DB
        media_file = MediaFile.objects.get(id=response.data['id'])
        self.assertEqual(media_file.uploaded_by, self.user)
        self.assertIsNotNone(media_file.file)

    def test_upload_missing_file_fails(self):
        url = reverse('mediafiles:upload')
        response = self.client.post(url, {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_rejected_when_quota_exceeded(self):
        url = reverse('mediafiles:upload')
        existing = SimpleUploadedFile(
            name='existing.bin',
            content=b'x' * 80,
            content_type='application/octet-stream',
        )
        MediaFile.objects.create(
            file=existing,
            original_name='existing.bin',
            file_type='application/octet-stream',
            file_size=80,
            uploaded_by=self.user,
        )

        incoming = SimpleUploadedFile(
            name='too_big.bin',
            content=b'y' * 30,
            content_type='application/octet-stream',
        )
        with override_settings(USER_STORAGE_QUOTA_BYTES=100):
            response = self.client.post(url, {'file': incoming}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(MediaFile.objects.filter(uploaded_by=self.user).count(), 1)
        self.assertIn('quota', str(response.data).lower())

    def test_upload_allowed_when_under_quota(self):
        url = reverse('mediafiles:upload')
        incoming = SimpleUploadedFile(
            name='ok.bin',
            content=b'z' * 20,
            content_type='application/octet-stream',
        )
        with override_settings(USER_STORAGE_QUOTA_BYTES=100):
            response = self.client.post(url, {'file': incoming}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MediaFile.objects.filter(uploaded_by=self.user).count(), 1)
