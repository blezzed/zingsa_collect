from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.releases.models import AppRelease

User = get_user_model()


def _apk(name="collect.apk", body=b"PK\x03\x04fake-apk"):
    return SimpleUploadedFile(name, body, content_type="application/vnd.android.package-archive")


class AppReleaseApiTests(APITestCase):
    def setUp(self):
        self.developer = User.objects.create_superuser(
            username="collect_developer",
            email="dev@example.com",
            password="password123",
        )
        self.field_user = User.objects.create_user(
            username="officer",
            email="officer@example.com",
            password="password123",
        )

    def test_public_latest_is_404_when_empty(self):
        url = reverse("releases:latest")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_developer_can_upload_and_public_can_download_latest(self):
        self.client.force_authenticate(user=self.developer)
        create_url = reverse("releases:list_create")
        response = self.client.post(
            create_url,
            {
                "version_name": "1.2.0",
                "version_code": "12",
                "notes": "First public build",
                "file": _apk(),
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data["version_name"], "1.2.0")
        self.assertEqual(response.data["version_code"], 12)
        self.assertTrue(response.data["is_latest"])
        self.assertTrue(response.data["download_url"])

        self.client.force_authenticate(user=None)
        latest = self.client.get(reverse("releases:latest"))
        self.assertEqual(latest.status_code, status.HTTP_200_OK)
        self.assertEqual(latest.data["version_name"], "1.2.0")
        listed = self.client.get(create_url)
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(len(listed.data), 1)

    def test_field_user_cannot_upload(self):
        self.client.force_authenticate(user=self.field_user)
        response = self.client.post(
            reverse("releases:list_create"),
            {
                "version_name": "1.0.0",
                "version_code": "1",
                "file": _apk(),
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_rejects_non_apk(self):
        self.client.force_authenticate(user=self.developer)
        response = self.client.post(
            reverse("releases:list_create"),
            {
                "version_name": "1.0.0",
                "version_code": "1",
                "file": SimpleUploadedFile(
                    "notes.txt", b"hello", content_type="text/plain"
                ),
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_developer_can_delete_release(self):
        self.client.force_authenticate(user=self.developer)
        created = self.client.post(
            reverse("releases:list_create"),
            {
                "version_name": "1.0.0",
                "version_code": "1",
                "file": _apk(),
            },
            format="multipart",
        )
        pk = created.data["id"]
        deleted = self.client.delete(
            reverse("releases:detail", kwargs={"pk": pk})
        )
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(AppRelease.objects.count(), 0)
