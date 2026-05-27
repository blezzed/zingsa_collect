import io
from django.urls import reverse
from django.contrib.auth import get_user_model
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
