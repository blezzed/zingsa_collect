"""Tests for maintenance mode middleware and owner bypass."""

from django.test import SimpleTestCase, override_settings
from django.urls import reverse


@override_settings(
    MAINTENANCE_MODE=True,
    MAINTENANCE_OWNER_TOKEN="test-owner-token-please-change",
    MAINTENANCE_MESSAGE="Collect is under maintenance.",
    MAINTENANCE_RETRY_AFTER=120,
    MAINTENANCE_BYPASS_COOKIE_NAME="collect_maintenance_bypass",
    ROOT_URLCONF="config.urls",
)
class MaintenanceModeTests(SimpleTestCase):
    def test_html_503_when_enabled(self):
        response = self.client.get("/", HTTP_ACCEPT="text/html")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response["Retry-After"], "120")
        self.assertContains(response, "We'll be right back", status_code=503)
        self.assertContains(response, "Collect is under maintenance.", status_code=503)

    def test_json_503_for_api(self):
        response = self.client.get("/api/docs/", HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response["Retry-After"], "120")
        self.assertEqual(response.json()["detail"], "maintenance")

    def test_header_bypass(self):
        response = self.client.get(
            "/api/docs/",
            HTTP_ACCEPT="application/json",
            HTTP_X_MAINTENANCE_OWNER_TOKEN="test-owner-token-please-change",
        )
        # Bypass reaches the view; may be 200 or redirect depending on auth,
        # but must not be the maintenance 503.
        self.assertNotEqual(response.status_code, 503)

    def test_bypass_cookie_exchange_and_clear(self):
        set_url = reverse("maintenance-bypass-set")
        response = self.client.get(
            set_url,
            {"token": "test-owner-token-please-change", "next": "/projects/"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/projects/")
        self.assertIn("collect_maintenance_bypass", response.cookies)

        # Cookie should allow normal responses.
        allowed = self.client.get("/api/docs/", HTTP_ACCEPT="application/json")
        self.assertNotEqual(allowed.status_code, 503)

        clear_url = reverse("maintenance-bypass-clear")
        cleared = self.client.get(clear_url)
        self.assertEqual(cleared.status_code, 302)

    def test_invalid_token_forbidden(self):
        set_url = reverse("maintenance-bypass-set")
        response = self.client.get(set_url, {"token": "wrong"})
        self.assertEqual(response.status_code, 403)

    def test_rejects_open_redirect(self):
        set_url = reverse("maintenance-bypass-set")
        response = self.client.get(
            set_url,
            {
                "token": "test-owner-token-please-change",
                "next": "https://evil.example/",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/")


@override_settings(MAINTENANCE_MODE=False)
class MaintenanceModeOffTests(SimpleTestCase):
    def test_passthrough_when_disabled(self):
        response = self.client.get("/", HTTP_ACCEPT="text/html")
        self.assertNotEqual(response.status_code, 503)
