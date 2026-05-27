import io
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection

from apps.forms.models import Form, FormVersion
from apps.projects.models import Project

User = get_user_model()

class BulkMediaSyncTests(APITestCase):
    def setUp(self):
        # 1. Setup User and Auth
        self.user = User.objects.create_user(username='mobileuser', password='password123')
        self.client.force_authenticate(user=self.user)

        # 2. Setup Project & Published Form with a media field
        self.project = Project.objects.create(name='Test Project', code='PROJ-MEDIA', owner=self.user)
        self.form = Form.objects.create(
            project=self.project,
            title='Media Form',
            slug='media-form',
            status='draft',
            created_by=self.user
        )
        schema = {
            'formId': str(self.form.id),
            'title': 'Media Form',
            'version': '1.0',
            'mode': 'form_first',
            'geometryType': 'none',
            'projectId': 'PROJ-MEDIA',
            'questions': [
                {'id': 'location_name', 'type': 'text', 'label': 'Name'},
                {'id': 'photo', 'type': 'image', 'label': 'Photo Evidence'}
            ]
        }
        from apps.forms.services.form_services import generate_column_mapping_service, calculate_form_checksum_service, generate_form_table_name_service, create_physical_form_table_service
        mapping, _ = generate_column_mapping_service(schema['questions'])
        
        self.version = FormVersion.objects.create(
            form=self.form,
            version_number=1,
            version_label="1.0",
            schema=schema,
            checksum=calculate_form_checksum_service(schema),
            column_mapping=mapping,
            created_by=self.user,
            is_published=True
        )
        self.version.physical_table_name = generate_form_table_name_service(self.form.slug, 1, self.form.id)
        self.version.save()
        create_physical_form_table_service(self.version)
        self.form.status = 'published'
        self.form.current_version = self.version
        self.form.submission_table_name = self.version.physical_table_name
        self.form.save()

    def test_mobile_media_bulk_sync_logic(self):
        """
        Simulates the mobile app's logic for syncing 10 records with media.
        """
        submissions_payload = []

        # STEP 1: Loop through all 10 local records. Upload their media files first.
        for i in range(1, 11):
            # Simulate mobile capturing a photo
            photo_file = SimpleUploadedFile(
                name=f'photo_{i}.jpg',
                content=f"fake_binary_data_{i}".encode('utf-8'),
                content_type='image/jpeg'
            )
            
            # Mobile hits the upload endpoint
            upload_url = reverse('mediafiles:upload')
            upload_response = self.client.post(upload_url, {'file': photo_file}, format='multipart')
            
            self.assertEqual(upload_response.status_code, status.HTTP_201_CREATED)
            
            # Mobile extracts the returned secure URL
            returned_url = upload_response.data['url']
            
            # Mobile prepares the JSON sync payload for this specific record
            submissions_payload.append({
                'client_submission_id': f'sub-media-{i}',
                'form_version_id': str(self.version.id),
                'answers': {
                    'location_name': f'Observation Point {i}',
                    'photo': returned_url  # Inject the URL instead of the binary file
                }
            })

        # STEP 2: Mobile does a single BULK sync of all JSON payloads
        sync_url = reverse('sync:bulk_sync')
        bulk_data = {
            'device_id': 'device-alpha',
            'submissions': submissions_payload
        }
        sync_response = self.client.post(sync_url, bulk_data, format='json')
        
        self.assertEqual(sync_response.status_code, status.HTTP_200_OK, sync_response.data)
        self.assertEqual(sync_response.data['total_success'], 10)
        self.assertEqual(sync_response.data['total_failed'], 0)

        # Verify Data in PostGIS Database
        table_name = self.version.physical_table_name
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT location_name, photo FROM {table_name} ORDER BY location_name ASC")
            rows = cursor.fetchall()
            
            self.assertEqual(len(rows), 10)
            self.assertEqual(rows[0][0], 'Observation Point 1')
            self.assertTrue('photo_1' in rows[0][1]) # URL contains the filename
