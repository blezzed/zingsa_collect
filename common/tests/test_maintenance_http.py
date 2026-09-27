import json

from django.test import SimpleTestCase, override_settings

TOKEN = "owner-token"


@override_settings(
    MAINTENANCE_MODE=True,
    MAINTENANCE_OWNER_TOKEN=TOKEN,
    MAINTENANCE_MESSAGE="ZINGSA Collect is down for maintenance.",
    MAINTENANCE_RETRY_AFTER=300,
    MAINTENANCE_BYPASS_COOKIE_NAME="zingsa_collect_maintenance_bypass",
    MAINTENANCE_BYPASS_COOKIE_MAX_AGE=604800,
    SESSION_COOKIE_SECURE=False,
)
class MaintenanceHttpTests(SimpleTestCase):
    def test_api_is_503_json(self):
        response = self.client.get("/api/forms/")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response["Retry-After"], "300")
        body = json.loads(response.content)
        self.assertEqual(body["detail"], "maintenance")
        self.assertIn("ZINGSA Collect", body["message"])

    def test_html_is_503_page(self):
        response = self.client.get("/admin/", HTTP_ACCEPT="text/html")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response["Retry-After"], "300")
        self.assertContains(response, "ZINGSA Collect is down for maintenance.", status_code=503)

    def test_accept_json_and_xhr(self):
        accept = self.client.get("/admin/", HTTP_ACCEPT="application/json")
        self.assertEqual(accept.status_code, 503)
        self.assertEqual(accept["Content-Type"], "application/json")
        xhr = self.client.get("/admin/", HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(xhr.status_code, 503)
        self.assertEqual(json.loads(xhr.content)["detail"], "maintenance")

    def test_header_bypass(self):
        blocked = self.client.get("/api/forms/", HTTP_X_MAINTENANCE_OWNER_TOKEN="")
        self.assertEqual(blocked.status_code, 503)
        allowed = self.client.get("/api/forms/", HTTP_X_MAINTENANCE_OWNER_TOKEN=TOKEN)
        self.assertNotEqual(allowed.status_code, 503)

    def test_wrong_token_is_403_and_does_not_set_cookie(self):
        response = self.client.post(
            "/__owner/maintenance-bypass/",
            {"token": "nope"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertNotIn("zingsa_collect_maintenance_bypass", response.cookies)

    def test_post_sets_httponly_cookie_and_redirects(self):
        response = self.client.post(
            "/__owner/maintenance-bypass/",
            {"token": TOKEN, "next": "/admin/"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/admin/")
        cookie = response.cookies["zingsa_collect_maintenance_bypass"]
        self.assertEqual(cookie.value, TOKEN)
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")
        self.assertEqual(cookie["secure"], "")

    def test_external_next_falls_back_to_admin(self):
        response = self.client.get(
            "/__owner/maintenance-bypass/",
            {"token": TOKEN, "next": "https://evil.test/phish"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/admin/")

    def test_cookie_bypass_then_clear(self):
        self.client.post("/__owner/maintenance-bypass/", {"token": TOKEN})
        allowed = self.client.get("/api/forms/")
        self.assertNotEqual(allowed.status_code, 503)
        cleared = self.client.post("/__owner/maintenance-bypass/clear/")
        self.assertEqual(cleared.status_code, 302)
        self.assertEqual(cleared["Location"], "/")
        blocked = self.client.get("/api/forms/")
        self.assertEqual(blocked.status_code, 503)

    @override_settings(MAINTENANCE_MODE=False)
    def test_off_does_not_block(self):
        response = self.client.get("/api/forms/")
        self.assertNotEqual(response.status_code, 503)
