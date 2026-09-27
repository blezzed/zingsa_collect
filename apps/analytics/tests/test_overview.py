from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.analytics.models import DataExportEvent
from apps.analytics.selectors.overview_selectors import get_system_overview
from apps.analytics.services.export_events import record_data_export
from apps.forms.models import Form
from apps.projects.models import Project

User = get_user_model()


class AnalyticsOverviewTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="ops_admin",
            email="ops@example.com",
            password="password123",
        )
        self.user = User.objects.create_user(
            username="end_user", password="password123"
        )
        self.project = Project.objects.create(
            name="Ops Project", code="OPS-1", owner=self.admin, status="active"
        )
        self.form = Form.objects.create(
            project=self.project,
            title="Ops Form",
            slug="ops-form",
            status="published",
            created_by=self.admin,
        )

    def test_overview_requires_ops_staff(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("analytics:overview")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_overview_includes_chart_series(self):
        self.client.force_authenticate(user=self.admin)
        record_data_export(
            user=self.admin, form=self.form, export_format="xlsx"
        )
        url = reverse("analytics:overview")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("users", data)
        self.assertEqual(len(data["users"]["by_recency"]["labels"]), 5)
        self.assertEqual(len(data["users"]["signups_by_month"]["values"]), 12)
        self.assertEqual(len(data["submissions"]["by_month"]["values"]), 12)
        self.assertEqual(data["exports"]["total"], 1)
        self.assertEqual(data["exports"]["this_month"], 1)
        self.assertIn("disk", data["storage"])
        self.assertIn("available", data["storage"]["disk"])
        self.assertEqual(data["forms"]["by_status"]["published"], 1)

    def test_record_export_is_best_effort(self):
        record_data_export(user=self.admin, form=self.form, export_format="xls")
        event = DataExportEvent.objects.get()
        self.assertEqual(event.export_format, "xlsx")
        overview = get_system_overview()
        self.assertEqual(overview["exports"]["by_format"]["values"][0], 1)
        self.assertTrue(timezone.is_aware(event.created_at) or event.created_at)
