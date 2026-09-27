import unittest

from common.maintenance import (
    is_bypass_path,
    safe_next,
    tokens_match,
    wants_maintenance_json,
)


class TokenMatchTests(unittest.TestCase):
    def test_rejects_empty_expected_or_provided(self):
        self.assertFalse(tokens_match("", "secret"))
        self.assertFalse(tokens_match("secret", ""))
        self.assertFalse(tokens_match("", ""))

    def test_matches_exact_token_only(self):
        self.assertTrue(tokens_match("secret", "secret"))
        self.assertFalse(tokens_match("secret", "Secret"))
        self.assertFalse(tokens_match("secret", "secret "))


class BypassPathTests(unittest.TestCase):
    def test_allows_both_owner_routes_with_or_without_slash(self):
        self.assertTrue(is_bypass_path("/__owner/maintenance-bypass/"))
        self.assertTrue(is_bypass_path("/__owner/maintenance-bypass"))
        self.assertTrue(is_bypass_path("/__owner/maintenance-bypass/clear/"))
        self.assertTrue(is_bypass_path("/__owner/maintenance-bypass/clear"))

    def test_other_paths_are_not_bypass(self):
        self.assertFalse(is_bypass_path("/admin/"))
        self.assertFalse(is_bypass_path("/api/forms/"))
        self.assertFalse(is_bypass_path("/__owner/maintenance-bypass/extra/"))


class JsonDecisionTests(unittest.TestCase):
    def test_api_accept_and_xhr(self):
        self.assertTrue(wants_maintenance_json(path="/api/forms/", accept="", requested_with=""))
        self.assertTrue(
            wants_maintenance_json(path="/admin/", accept="application/json", requested_with="")
        )
        self.assertTrue(
            wants_maintenance_json(
                path="/admin/",
                accept="text/html",
                requested_with="XMLHttpRequest",
            )
        )
        self.assertFalse(
            wants_maintenance_json(path="/admin/", accept="text/html", requested_with="")
        )


class SafeNextTests(unittest.TestCase):
    def test_relative_path(self):
        self.assertEqual(safe_next("/admin/auth/user/"), "/admin/auth/user/")

    def test_rejects_external_and_empty(self):
        self.assertEqual(safe_next("https://evil.test"), "/admin/")
        self.assertEqual(safe_next("//evil.test"), "/admin/")
        self.assertEqual(safe_next(""), "/admin/")
        self.assertEqual(safe_next(None), "/admin/")
