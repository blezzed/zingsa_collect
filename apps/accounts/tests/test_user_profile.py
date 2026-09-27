from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.mediafiles.models import MediaFile
from apps.organizations.models import Organization, OrganizationMember

User = get_user_model()


class UserProfileViewTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="ops_admin",
            email="ops@example.com",
            password="password123",
        )
        self.target = User.objects.create_user(
            username="dinhidzatinotenda11@gmail.com",
            email="dinhidzatinotenda11@gmail.com",
            password="password123",
            first_name="Tinotenda",
            organization_type="ngo",
        )
        self.org = Organization.objects.create(
            name="ZINGSA",
            code="ZINGSA-ORG",
        )
        OrganizationMember.objects.create(
            organization=self.org,
            user=self.target,
            role="member",
        )
        MediaFile.objects.create(
            file=SimpleUploadedFile("note.txt", b"hello", content_type="text/plain"),
            original_name="note.txt",
            file_type="text/plain",
            file_size=5,
            uploaded_by=self.target,
        )

    def test_superuser_can_view_profile_with_org_and_usage(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse(
            "accounts:user_profile",
            kwargs={"username": self.target.username},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["username"], self.target.username)
        self.assertEqual(response.data["organization_type"], "ngo")
        self.assertEqual(len(response.data["organizations"]), 1)
        self.assertEqual(response.data["organizations"][0]["name"], "ZINGSA")
        self.assertEqual(response.data["organizations"][0]["role"], "member")
        usage = response.data["usage"]
        self.assertEqual(usage["storage_bytes"], 5)
        self.assertEqual(usage["file_count"], 1)
        self.assertEqual(usage["storage_quota_bytes"], 10 * 1024 * 1024 * 1024)
        self.assertEqual(
            usage["storage_remaining_bytes"],
            usage["storage_quota_bytes"] - 5,
        )
        self.assertIn("submissions_by_month", usage)
        self.assertEqual(len(usage["submissions_by_month"]["values"]), 12)

    def test_non_manager_cannot_view_profile(self):
        self.client.force_authenticate(user=self.target)
        url = reverse(
            "accounts:user_profile",
            kwargs={"username": self.admin.username},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AccountUsageQuotaTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="collector",
            password="password123",
        )
        self.client.force_authenticate(user=self.user)

    def test_own_usage_includes_10gb_quota(self):
        url = reverse("accounts:account_usage")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["storage_quota_bytes"], 10 * 1024 * 1024 * 1024)
        self.assertEqual(response.data["storage_bytes"], 0)
        self.assertEqual(response.data["storage_remaining_bytes"], 10 * 1024 * 1024 * 1024)
        self.assertEqual(response.data["submissions_total"], 0)
