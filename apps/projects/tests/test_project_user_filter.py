from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.organizations.models import Organization
from apps.projects.models import Project, ProjectMember

User = get_user_model()


class ProjectUserFilterTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="ops_admin",
            email="ops@example.com",
            password="password123",
        )
        self.owner = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="password123",
            first_name="Alice",
            last_name="Ng",
        )
        self.member = User.objects.create_user(
            username="bob", password="password123"
        )
        self.other = User.objects.create_user(
            username="carol", password="password123"
        )
        self.org = Organization.objects.create(name="Filter Org")
        self.owned = Project.objects.create(
            name="Alice owned",
            code="ALICE-1",
            owner=self.owner,
            organization=self.org,
            status="active",
        )
        self.shared = Project.objects.create(
            name="Shared with Alice",
            code="SHARE-1",
            owner=self.other,
            organization=self.org,
            status="draft",
        )
        ProjectMember.objects.create(
            project=self.shared, user=self.owner, role="collector"
        )
        Project.objects.create(
            name="Unrelated",
            code="NONE-1",
            owner=self.other,
            organization=self.org,
        )

    def test_superuser_can_filter_projects_by_user(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("projects:list_create")
        response = self.client.get(url, {"user": self.owner.id, "page_size": 50})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = {row["name"] for row in response.data["results"]}
        self.assertEqual(names, {"Alice owned", "Shared with Alice"})
        profile = response.data["filter_user"]
        self.assertEqual(profile["username"], "alice")
        self.assertEqual(profile["email"], "alice@example.com")
        self.assertEqual(profile["owned_project_count"], 1)
        self.assertEqual(profile["member_project_count"], 1)

    def test_non_superuser_ignores_user_filter(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse("projects:list_create")
        response = self.client.get(url, {"user": self.other.id, "page_size": 50})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = {row["name"] for row in response.data["results"]}
        self.assertIn("Alice owned", names)
        self.assertNotIn("filter_user", response.data)
