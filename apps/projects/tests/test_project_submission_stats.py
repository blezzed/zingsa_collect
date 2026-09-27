from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.forms.models import Form, FormVersion
from apps.organizations.models import Organization
from apps.projects.models import Project
from apps.submissions.models import SubmissionIndex, SubmissionMedia

User = get_user_model()


class ProjectSubmissionStatsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="owner", password="password123"
        )
        self.org = Organization.objects.create(name="Stats Org", code="STATS-ORG")
        self.project = Project.objects.create(
            name="Counted project",
            code="COUNT-1",
            owner=self.user,
            organization=self.org,
            status="active",
        )
        empty = Project.objects.create(
            name="Empty project",
            code="EMPTY-1",
            owner=self.user,
            organization=self.org,
            status="draft",
        )
        self.empty_id = str(empty.id)
        form = Form.objects.create(
            project=self.project,
            title="Count form",
            slug="count-form",
            created_by=self.user,
        )
        version = FormVersion.objects.create(
            form=form,
            version_number=1,
            version_label="1.0",
            schema={"questions": []},
            checksum="abc",
            created_by=self.user,
        )
        first = SubmissionIndex.objects.create(
            project=self.project,
            form=form,
            form_version=version,
            device_id="dev-1",
            client_submission_id="sub-1",
            physical_table_name="t",
            physical_row_id=1,
        )
        SubmissionIndex.objects.create(
            project=self.project,
            form=form,
            form_version=version,
            device_id="dev-1",
            client_submission_id="sub-2",
            physical_table_name="t",
            physical_row_id=2,
        )
        SubmissionMedia.objects.create(
            submission_index=first,
            field_id="photo",
            file_type="image",
            original_name="a.jpg",
            mime_type="image/jpeg",
            size=2048,
        )
        SubmissionMedia.objects.create(
            submission_index=first,
            field_id="photo2",
            file_type="image",
            original_name="b.jpg",
            mime_type="image/jpeg",
            size=1024,
        )
        self.client.force_authenticate(user=self.user)

    def test_list_includes_submission_count_and_bytes(self):
        url = reverse("projects:list_create")
        response = self.client.get(url, {"page_size": 50})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        by_id = {row["id"]: row for row in response.data["results"]}
        counted = by_id[str(self.project.id)]
        empty = by_id[self.empty_id]
        self.assertEqual(counted["submission_count"], 2)
        self.assertEqual(counted["submission_bytes"], 3072)
        self.assertEqual(empty["submission_count"], 0)
        self.assertEqual(empty["submission_bytes"], 0)

    def test_detail_includes_submission_stats(self):
        url = reverse("projects:detail", kwargs={"pk": self.project.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["submission_count"], 2)
        self.assertEqual(response.data["submission_bytes"], 3072)

    def test_form_list_includes_submission_stats(self):
        url = reverse(
            "projects:form_list_create", kwargs={"project_id": self.project.id}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["submission_count"], 2)
        self.assertEqual(response.data[0]["submission_bytes"], 3072)
