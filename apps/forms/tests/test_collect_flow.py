import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.db import connection
from django.urls import reverse
from psycopg2 import sql
from rest_framework import status
from rest_framework.test import APITestCase

from apps.forms.models import Form, FormVersion
from apps.organizations.models import Organization, OrganizationMember
from apps.projects.models import Project, ProjectMember
from apps.submissions.models import SubmissionIndex

User = get_user_model()

FULL_CLEAN_PATH = Path(__file__).resolve().parents[3] / 'full_clean.json'


def load_flat_form_payload(key: str = 'test_form_1') -> dict:
    """Load a flat mobile form schema from full_clean.json."""
    with FULL_CLEAN_PATH.open(encoding='utf-8') as f:
        data = json.load(f)
    return data[key]


class ZingsaCollectFlowTestCase(APITestCase):
    """End-to-end API flow: auth → org → project → form → publish → sync."""

    def setUp(self):
        self.password = 'SecureTestPass123!'
        self.user_data = {
            'username': 'field_officer_01',
            'email': 'officer@zingsa.test',
            'password': self.password,
            're_password': self.password,
        }

    def _register_user(self):
        url = reverse('user-list')
        return self.client.post(url, self.user_data, format='json')

    def _login(self):
        url = reverse('jwt-create')
        return self.client.post(
            url,
            {'username': self.user_data['username'], 'password': self.password},
            format='json',
        )

    def _auth_headers(self, access_token: str) -> dict:
        return {'HTTP_AUTHORIZATION': f'Bearer {access_token}'}

    def test_complete_collect_api_flow(self):
        # --- 1. Auth: Registration ---
        reg_response = self._register_user()
        self.assertEqual(reg_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(reg_response.data['username'], self.user_data['username'])
        user = User.objects.get(username=self.user_data['username'])

        # --- 1. Auth: JWT Login ---
        login_response = self._login()
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', login_response.data)
        self.assertIn('refresh', login_response.data)
        access = login_response.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

        # --- 2. Organization Creation ---
        org_payload = {'name': 'Test Mapping Org'}
        org_url = reverse('organizations:list_create')
        org_response = self.client.post(org_url, org_payload, format='json')
        self.assertEqual(org_response.status_code, status.HTTP_201_CREATED)
        org_id = org_response.data['id']
        self.assertEqual(org_response.data['name'], org_payload['name'])
        self.assertTrue(org_response.data['code'].startswith('ORG-'))

        membership = OrganizationMember.objects.get(organization_id=org_id, user=user)
        self.assertEqual(membership.role, 'admin')

        # --- 3. Project Creation ---
        project_payload = {
            'name': 'Wildlife Monitoring',
            'description': 'Monitoring wild species.',
            'organization': org_id,
            'status': 'active',
        }
        project_url = reverse('projects:list_create')
        project_response = self.client.post(project_url, project_payload, format='json')
        self.assertEqual(project_response.status_code, status.HTTP_201_CREATED)
        project_id = project_response.data['id']
        project_code = project_response.data['code']
        self.assertTrue(project_code.startswith('PROJ-'))

        project = Project.objects.get(id=project_id)
        self.assertEqual(project.owner, user)
        pm = ProjectMember.objects.get(project=project, user=user)
        self.assertEqual(pm.role, 'manager')

        # --- 4. Form Creation (flat JSON from full_clean.json) ---
        form_data = load_flat_form_payload('test_form_1')
        form_data['projectId'] = project_code
        form_data['geometryType'] = 'mixed'

        forms_url = reverse('projects:form_list_create', kwargs={'project_id': project_id})
        
        # Test Validation Failure (empty title)
        bad_form_data = dict(form_data)
        bad_form_data['title'] = "   "
        response = self.client.post(forms_url, bad_form_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test Validation Failure (empty question label)
        bad_form_data = dict(form_data)
        bad_form_data['title'] = "Wildlife Observation"
        bad_form_data['questions'] = [{"id": "q1", "type": "text", "label": ""}]
        response = self.client.post(forms_url, bad_form_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Now create valid form
        form_response = self.client.post(forms_url, form_data, format='json')
        self.assertEqual(form_response.status_code, status.HTTP_201_CREATED)
        form_id = form_response.data['id']
        self.assertEqual(form_response.data['title'], form_data['title'])
        self.assertEqual(form_response.data['slug'], 'community-gis-survey')

        form = Form.objects.get(id=form_id)
        self.assertEqual(form.status, 'draft')
        self.assertEqual(form.versions.count(), 1)
        draft_version = form.current_version
        self.assertFalse(draft_version.is_published)
        self.assertIn('location_name', draft_version.column_mapping)
        self.assertIn('propertyLine', draft_version.column_mapping)
        self.assertIn('propertyPolygon', draft_version.column_mapping)

        # --- 5. Form Publishing (dynamic table) ---
        publish_url = reverse('forms:publish', kwargs={'pk': form_id})
        publish_response = self.client.post(publish_url, format='json')
        self.assertEqual(publish_response.status_code, status.HTTP_200_OK)
        self.assertIn('physical_table_name', publish_response.data)

        form.refresh_from_db()
        self.assertEqual(form.status, 'published')
        active_version = form.current_version
        self.assertTrue(active_version.is_published)
        self.assertIsNotNone(active_version.physical_table_name)
        self.assertTrue(active_version.physical_table_name.startswith('collect_community_gis_survey_v1_'))
        table_name = active_version.physical_table_name
        self.assertIsNotNone(table_name)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = %s
                )
                """,
                [table_name],
            )
            self.assertTrue(cursor.fetchone()[0])

            cursor.execute(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = %s
                """,
                [table_name],
            )
            cols = {row[0]: row[1] for row in cursor.fetchall()}
            self.assertIn('location_name', cols)
            self.assertIn('propertyline', cols)
            self.assertIn('propertypolygon', cols)
            self.assertEqual(cols['propertyline'], 'USER-DEFINED')
            self.assertEqual(cols['propertypolygon'], 'USER-DEFINED')

        # --- 6. Sync submission into dynamic table ---
        submission_data = {
            'device_id': 'device-officer-alpha',
            'client_submission_id': 'sub-gis-001',
            'form_version_id': str(active_version.id),
            'answers': {
                'location_name': 'Harare CBD Survey Point',
                'coordinates': '-17.8252, 31.0335',
                'land_use': 'commercial',
                'description': 'Central business district mapping node.',
            },
        }
        sync_url = reverse('sync:single_sync')
        sync_response = self.client.post(sync_url, submission_data, format='json')
        self.assertEqual(sync_response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(sync_response.data['is_duplicate'])

        sub_index = SubmissionIndex.objects.get(id=sync_response.data['submission']['id'])
        self.assertEqual(sub_index.sync_status, 'synced')

        with connection.cursor() as cursor:
            query = sql.SQL(
                "SELECT id, location_name, land_use FROM {} WHERE id = %s"
            ).format(sql.Identifier(table_name))
            cursor.execute(query, [sub_index.physical_row_id])
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[1], 'Harare CBD Survey Point')
            self.assertEqual(row[2], 'commercial')

        # Duplicate sync should be idempotent
        dup_response = self.client.post(sync_url, submission_data, format='json')
        self.assertEqual(dup_response.status_code, status.HTTP_200_OK)
        self.assertTrue(dup_response.data['is_duplicate'])
