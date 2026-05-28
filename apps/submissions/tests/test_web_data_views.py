import json
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.forms.models import Form, FormVersion
from apps.projects.models import Project
from apps.submissions.services.submission_services import sync_submission_to_physical_table_service
from apps.forms.services.form_services import generate_column_mapping_service, calculate_form_checksum_service, generate_form_table_name_service, create_physical_form_table_service

User = get_user_model()

class WebDataViewsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='webuser', password='password123')
        self.client.force_authenticate(user=self.user)

        self.project = Project.objects.create(name='Web Project', code='WEB-1', owner=self.user)
        self.form = Form.objects.create(
            project=self.project,
            title='Geo Form',
            slug='geo-form',
            status='draft',
            geometry_type='point',
            created_by=self.user
        )
        schema = {
            'formId': str(self.form.id),
            'title': 'Geo Form',
            'version': '1.0',
            'mode': 'map_first',
            'geometryType': 'point',
            'projectId': 'WEB-1',
            'questions': [
                {'id': 'location_name', 'type': 'text', 'label': 'Name'},
                {'id': 'geom_point', 'type': 'point', 'label': 'Location Point'}
            ]
        }
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

        # Seed 5 records
        for i in range(1, 6):
            sync_submission_to_physical_table_service(
                client_submission_id=f'sub-{i}',
                device_id='device-1',
                form_version=self.version,
                answers={
                    'location_name': f'Point {i}',
                    'geom_point': {'type': 'Point', 'coordinates': [31.0 + i, -17.0 - i]}
                },
                user=self.user
            )

    def test_geojson_endpoint(self):
        url = reverse('web_data:geojson', kwargs={'form_id': self.form.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['type'], 'FeatureCollection')
        self.assertEqual(len(data['features']), 5)
        self.assertEqual(data['features'][0]['type'], 'Feature')
        self.assertIn('geometry', data['features'][0])
        self.assertEqual(data['features'][0]['geometry']['type'], 'Point')
        self.assertIn('id', data['features'][0]['properties'])
        self.assertNotIn('location_name', data['features'][0]['properties']) # Ensure attributes are stripped

    def test_columns_endpoint(self):
        url = reverse('web_data:columns', kwargs={'form_id': self.form.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        col_names = [col['label'] for col in data]
        self.assertIn('Name', col_names)
        self.assertIn('Location Point', col_names)
        self.assertIn('ID', col_names)

    def test_paginated_data_endpoint(self):
        url = reverse('web_data:data_paginated', kwargs={'form_id': self.form.id})
        response = self.client.get(f"{url}?page=1&limit=2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['total'], 5)
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['limit'], 2)
        self.assertEqual(len(data['data']), 2)
        
        # Verify geometry column is stripped from attribute data
        row = data['data'][0]
        self.assertIn('location_name', row)
        self.assertNotIn('geom_point', row)

    def test_detail_data_endpoint(self):
        # First get the paginated data to extract a physical ID
        url_paginated = reverse('web_data:data_paginated', kwargs={'form_id': self.form.id})
        res_paginated = self.client.get(url_paginated).json()
        row_id = res_paginated['data'][0]['id']
        
        url_detail = reverse('web_data:data_detail', kwargs={'form_id': self.form.id, 'row_id': row_id})
        response = self.client.get(url_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('metadata', data)
        self.assertIn('answers', data)
        self.assertIn('geom_point', data['answers']) # Detail view MUST include geometry
