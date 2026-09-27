from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class UserCreateProfileFieldsTests(APITestCase):
    def test_register_persists_first_and_last_name(self):
        url = reverse("user-list")
        response = self.client.post(
            url,
            {
                "username": "new_collector",
                "email": "collector@zingsa.test",
                "password": "SecureTestPass123!",
                "re_password": "SecureTestPass123!",
                "first_name": "Tinotenda",
                "last_name": "Dinhidza",
                "country": "Zimbabwe",
                "sector": "agriculture",
                "organization_type": "ngo",
                "newsletter_opt_in": False,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data.get("first_name"), "Tinotenda")
        self.assertEqual(response.data.get("last_name"), "Dinhidza")

        user = User.objects.get(username="new_collector")
        self.assertEqual(user.first_name, "Tinotenda")
        self.assertEqual(user.last_name, "Dinhidza")
        self.assertEqual(user.country, "Zimbabwe")

        login = self.client.post(
            reverse("jwt-create"),
            {"username": "new_collector", "password": "SecureTestPass123!"},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertEqual(login.data["user"]["first_name"], "Tinotenda")
        self.assertEqual(login.data["user"]["last_name"], "Dinhidza")
