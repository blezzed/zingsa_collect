from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.projects.models import Project

User = get_user_model()


class ProjectNameUniquePerOwnerTests(APITestCase):
    def setUp(self):
        self.alice = User.objects.create_user(
            username="alice", password="password123"
        )
        self.bob = User.objects.create_user(
            username="bob", password="password123"
        )
        Project.objects.create(
            name="Demo project",
            code="DEMO-ALICE",
            owner=self.alice,
        )

    def test_other_user_can_reuse_demo_project_name(self):
        self.client.force_authenticate(user=self.bob)
        response = self.client.post(
            reverse("projects:list_create"),
            {"name": "Demo project"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data["name"], "Demo project")
        self.assertEqual(
            Project.objects.filter(name__iexact="Demo project").count(), 2
        )

    def test_same_owner_cannot_reuse_project_name(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.post(
            reverse("projects:list_create"),
            {"name": "Demo Project"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)
