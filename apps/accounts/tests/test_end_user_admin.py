from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.mediafiles.models import MediaFile
from apps.organizations.models import Organization, OrganizationMember
from apps.projects.models import Project, ProjectMember

User = get_user_model()


class EndUserAdminListTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="ops_admin",
            email="ops@example.com",
            password="password123",
        )
        self.end_user = User.objects.create_user(
            username="collector",
            email="collector@example.com",
            password="password123",
            first_name="Ada",
            last_name="Cole",
            country="Zimbabwe",
            city="Harare",
            sector="ngo",
            organization_type="ngo",
        )
        self.org = Organization.objects.create(name="ZINGSA", code="ZINGSA-STAFF")
        OrganizationMember.objects.create(
            organization=self.org, user=self.end_user, role="member"
        )
        owned = Project.objects.create(
            name="Owned",
            code="OWN-1",
            owner=self.end_user,
            organization=self.org,
            status="active",
        )
        other_owner = User.objects.create_user(
            username="other", password="password123"
        )
        shared = Project.objects.create(
            name="Shared",
            code="SHR-1",
            owner=other_owner,
            organization=self.org,
            status="active",
        )
        ProjectMember.objects.create(
            project=shared, user=self.end_user, role="collector"
        )
        MediaFile.objects.create(
            file=SimpleUploadedFile("a.bin", b"hello", content_type="text/plain"),
            original_name="a.bin",
            file_type="text/plain",
            file_size=5,
            uploaded_by=self.end_user,
        )

    def test_list_includes_usage_projects_and_orgs(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("accounts:users_admin_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        row = next(item for item in response.data if item["username"] == "collector")
        self.assertEqual(row["first_name"], "Ada")
        self.assertEqual(row["country"], "Zimbabwe")
        self.assertEqual(row["owned_project_count"], 1)
        self.assertEqual(row["member_project_count"], 1)
        self.assertEqual(row["storage_bytes"], 5)
        self.assertEqual(row["file_count"], 1)
        self.assertEqual(row["storage_quota_bytes"], 10 * 1024 * 1024 * 1024)
        self.assertEqual(row["organizations"][0]["name"], "ZINGSA")
        self.assertEqual(row["submission_count"], 0)

    def test_non_manager_forbidden(self):
        self.client.force_authenticate(user=self.end_user)
        url = reverse("accounts:users_admin_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_storage_list(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("accounts:users_storage")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["complete"])
        self.assertEqual(response.data["quota_bytes"], 10 * 1024 * 1024 * 1024)
        by_name = {row["username"]: row for row in response.data["users"]}
        self.assertEqual(by_name["collector"]["storage_bytes"], 5)
        self.assertEqual(by_name["collector"]["file_count"], 1)
