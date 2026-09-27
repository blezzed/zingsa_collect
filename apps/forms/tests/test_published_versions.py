from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.forms.models import Form, FormVersion
from apps.forms.services.form_services import (
    get_latest_published_version,
    publish_form_service,
    update_form_service,
)
from apps.organizations.models import Organization
from apps.projects.models import Project

User = get_user_model()


class PublishedVersionCollectorTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="publisher",
            email="publisher@example.com",
            password="pass12345",
        )
        self.org = Organization.objects.create(name="Org", code="org1")
        self.project = Project.objects.create(
            name="Project",
            code="proj1",
            organization=self.org,
            owner=self.user,
            status="active",
        )
        self.form = Form.objects.create(
            project=self.project,
            title="Survey",
            slug="survey",
            created_by=self.user,
            status="draft",
            geometry_type="none",
            # Unauthenticated available endpoint only returns demo forms.
            is_demo=True,
        )
        schema_v1 = {
            "formId": str(self.form.id),
            "title": "Survey",
            "version": "1.0",
            "mode": "form_first",
            "projectId": self.project.code,
            "geometryType": "none",
            "questions": [{"id": "q1", "type": "text", "label": "Name", "required": False}],
        }
        v1 = FormVersion.objects.create(
            form=self.form,
            version_number=1,
            version_label="1.0",
            schema=schema_v1,
            checksum="c1",
            is_published=False,
            column_mapping={"q1": "q1"},
            created_by=self.user,
        )
        self.form.current_version = v1
        self.form.save(update_fields=["current_version"])

    @patch("apps.forms.services.form_services.migrate_submissions_between_tables")
    @patch("apps.forms.services.form_services.ensure_physical_columns_service")
    @patch("apps.forms.services.form_services.create_physical_form_table_service")
    def test_publish_supersedes_previous_published_version(
        self, _create_table, _ensure_cols, _migrate
    ):
        v1 = publish_form_service(self.form, created_by=self.user)
        self.form.refresh_from_db()
        self.assertTrue(v1.is_published)

        schema_v2 = dict(v1.schema)
        schema_v2["questions"] = [
            {"id": "q1", "type": "text", "label": "Name", "required": False},
            {"id": "q2", "type": "text", "label": "Age", "required": False},
        ]
        update_form_service(self.form, {}, schema=schema_v2, user=self.user)
        self.form.refresh_from_db()
        v2 = publish_form_service(self.form, created_by=self.user)

        v1.refresh_from_db()
        self.assertFalse(v1.is_published)
        self.assertTrue(v2.is_published)
        self.assertEqual(get_latest_published_version(self.form).id, v2.id)
        self.assertEqual(self.form.versions.filter(is_published=True).count(), 1)

    @patch("apps.forms.services.form_services.migrate_submissions_between_tables")
    @patch("apps.forms.services.form_services.ensure_physical_columns_service")
    @patch("apps.forms.services.form_services.create_physical_form_table_service")
    def test_can_rename_published_form_when_adding_a_version(
        self, _create_table, _ensure_cols, _migrate
    ):
        publish_form_service(self.form, created_by=self.user)
        self.form.refresh_from_db()
        published = self.form.current_version
        self.assertTrue(published.is_published)

        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.patch(
            reverse("forms:detail", kwargs={"pk": self.form.id}),
            {
                "title": "Household survey 2026",
                "description": "Updated after first publish",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["title"], "Household survey 2026")
        self.assertEqual(
            response.data["description"], "Updated after first publish"
        )

        self.form.refresh_from_db()
        self.assertEqual(self.form.title, "Household survey 2026")
        self.assertEqual(self.form.description, "Updated after first publish")
        draft = self.form.current_version
        self.assertFalse(draft.is_published)
        self.assertNotEqual(draft.id, published.id)
        self.assertEqual(draft.schema["title"], "Household survey 2026")
        self.assertEqual(
            draft.schema["description"], "Updated after first publish"
        )

    @patch("apps.forms.services.form_services.migrate_submissions_between_tables")
    @patch("apps.forms.services.form_services.ensure_physical_columns_service")
    @patch("apps.forms.services.form_services.create_physical_form_table_service")
    def test_available_endpoint_points_at_latest_published_only(
        self, _create_table, _ensure_cols, _migrate
    ):
        v1 = publish_form_service(self.form, created_by=self.user)
        schema_v2 = dict(v1.schema)
        schema_v2["questions"] = list(schema_v2["questions"]) + [
            {"id": "q2", "type": "text", "label": "Age", "required": False}
        ]
        update_form_service(self.form, {}, schema=schema_v2, user=self.user)
        self.form.refresh_from_db()
        v2 = publish_form_service(self.form, created_by=self.user)

        client = APIClient()
        url = reverse("forms:available")
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        row = response.data[0]
        self.assertEqual(row["current_version"], str(v2.id))
        self.assertEqual(row["published_version_number"], v2.version_number)
        self.assertEqual(row["published_checksum"], v2.checksum)
        self.assertTrue(row["force_update"])
        self.assertEqual(
            row["current_version_details"]["version_number"],
            v2.version_number,
        )

        download = client.get(reverse("forms:download", kwargs={"pk": self.form.id}))
        self.assertEqual(download.status_code, status.HTTP_200_OK)
        self.assertEqual(download.data["version_id"], str(v2.id))
        self.assertEqual(download.data["version_number"], v2.version_number)
        self.assertTrue(download.data["force_update"])
        self.assertTrue(download.data["is_latest"])

    @patch("apps.forms.services.form_services.migrate_submissions_between_tables")
    @patch("apps.forms.services.form_services.ensure_physical_columns_service")
    @patch("apps.forms.services.form_services.create_physical_form_table_service")
    def test_draft_project_forms_hidden_from_mobile(
        self, _create_table, _ensure_cols, _migrate
    ):
        publish_form_service(self.form, created_by=self.user)
        self.project.status = "draft"
        self.project.save(update_fields=["status"])

        client = APIClient()
        available = client.get(reverse("forms:available"))
        self.assertEqual(available.status_code, status.HTTP_200_OK)
        self.assertEqual(available.data, [])

        download = client.get(reverse("forms:download", kwargs={"pk": self.form.id}))
        self.assertEqual(download.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.forms.services.form_services.migrate_submissions_between_tables")
    @patch("apps.forms.services.form_services.ensure_physical_columns_service")
    @patch("apps.forms.services.form_services.create_physical_form_table_service")
    def test_authenticated_user_only_sees_own_collector_projects(
        self, _create_table, _ensure_cols, _migrate
    ):
        from apps.projects.models import ProjectMember

        # Non-demo form on owner's active project
        self.form.is_demo = False
        self.form.save(update_fields=["is_demo"])
        publish_form_service(self.form, created_by=self.user)

        other_owner = User.objects.create_user(
            username="other_owner",
            email="other@example.com",
            password="pass12345",
        )
        stranger = User.objects.create_user(
            username="stranger",
            email="stranger@example.com",
            password="pass12345",
        )
        collector = User.objects.create_user(
            username="collector",
            email="collector@example.com",
            password="pass12345",
        )
        viewer = User.objects.create_user(
            username="viewer",
            email="viewer@example.com",
            password="pass12345",
        )

        other_project = Project.objects.create(
            name="Other Project",
            code="proj2",
            organization=self.org,
            owner=other_owner,
            status="active",
        )
        other_form = Form.objects.create(
            project=other_project,
            title="Other Survey",
            slug="other-survey",
            created_by=other_owner,
            status="draft",
            geometry_type="none",
            is_demo=False,
        )
        other_version = FormVersion.objects.create(
            form=other_form,
            version_number=1,
            version_label="1.0",
            schema={
                "formId": str(other_form.id),
                "title": "Other Survey",
                "version": "1.0",
                "mode": "form_first",
                "projectId": other_project.code,
                "geometryType": "none",
                "questions": [{"id": "q1", "type": "text", "label": "Name", "required": False}],
            },
            checksum="c-other",
            is_published=False,
            column_mapping={"q1": "q1"},
            created_by=other_owner,
        )
        other_form.current_version = other_version
        other_form.save(update_fields=["current_version"])
        publish_form_service(other_form, created_by=other_owner)

        ProjectMember.objects.create(
            project=self.project, user=collector, role="collector"
        )
        ProjectMember.objects.create(
            project=self.project, user=viewer, role="viewer"
        )

        client = APIClient()

        client.force_authenticate(user=stranger)
        denied = client.get(reverse("forms:available"))
        self.assertEqual(denied.status_code, status.HTTP_200_OK)
        self.assertEqual(denied.data, [])
        denied_dl = client.get(reverse("forms:download", kwargs={"pk": self.form.id}))
        self.assertEqual(denied_dl.status_code, status.HTTP_400_BAD_REQUEST)

        client.force_authenticate(user=viewer)
        viewer_list = client.get(reverse("forms:available"))
        self.assertEqual(viewer_list.data, [])

        client.force_authenticate(user=collector)
        collector_list = client.get(reverse("forms:available"))
        self.assertEqual(len(collector_list.data), 1)
        self.assertEqual(collector_list.data[0]["id"], str(self.form.id))

        client.force_authenticate(user=self.user)
        owner_list = client.get(reverse("forms:available"))
        ids = {row["id"] for row in owner_list.data}
        self.assertEqual(ids, {str(self.form.id)})
        self.assertNotIn(str(other_form.id), ids)
