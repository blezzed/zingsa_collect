from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.feedback.models import Feedback

User = get_user_model()


class FeedbackStatusTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="ops_admin",
            email="ops@example.com",
            password="password123",
        )
        self.author = User.objects.create_user(
            username="alice", password="password123"
        )
        self.item = Feedback.objects.create(
            user=self.author,
            category=Feedback.Category.BUG,
            subject="Map is slow",
            message="The map takes too long to load on mobile.",
        )

    def test_staff_can_mark_solved(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("feedback:detail", kwargs={"pk": self.item.id})
        response = self.client.patch(url, {"status": "solved"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "solved")
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, Feedback.Status.SOLVED)
        self.assertEqual(self.item.resolved_by_id, self.admin.id)

    def test_author_cannot_patch_status(self):
        self.client.force_authenticate(user=self.author)
        url = reverse("feedback:detail", kwargs={"pk": self.item.id})
        response = self.client.patch(url, {"status": "solved"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_must_provide_reason_to_ignore(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("feedback:detail", kwargs={"pk": self.item.id})
        response = self.client.patch(url, {"status": "ignored"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.patch(
            url,
            {"status": "ignored", "note": "Duplicate of an existing ticket."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ignored")
        self.assertEqual(
            response.data["status_note"], "Duplicate of an existing ticket."
        )

    def test_staff_can_filter_by_status(self):
        Feedback.objects.create(
            user=self.author,
            category=Feedback.Category.IMPROVEMENT,
            subject="Add export",
            message="Please add a GeoPackage export option.",
            status=Feedback.Status.SOLVED,
        )
        self.client.force_authenticate(user=self.admin)
        url = reverse("feedback:list_create")
        response = self.client.get(url, {"status": "open"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        subjects = {row["subject"] for row in response.data["results"]}
        self.assertEqual(subjects, {"Map is slow"})
