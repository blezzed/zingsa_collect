from pathlib import Path

from django.test import SimpleTestCase

from common.spa_views import _candidate_files, _safe_join


class SpaCandidateTests(SimpleTestCase):
    def setUp(self):
        self.root = Path(self._get_temp_dir_root())
        self.root.mkdir(parents=True, exist_ok=True)

    def _get_temp_dir_root(self) -> str:
        import tempfile

        return tempfile.mkdtemp(prefix="ux_ui_test_")

    def _rels(self, resource: str) -> list[str]:
        candidates = _candidate_files(self.root, resource)
        return [
            c.relative_to(self.root.resolve()).as_posix()
            for c in candidates
        ]

    def test_forms_uuid_falls_back_to_placeholder(self):
        rels = self._rels("forms/f94cb5ef-de5d-4849-8337-ba3def4d3453/")
        self.assertIn("forms/_/index.html", rels)

    def test_projects_nested_fallback(self):
        rels = self._rels("projects/abc-123/settings/")
        self.assertIn("projects/_/settings/index.html", rels)

    def test_safe_join_rejects_escape(self):
        self.assertIsNone(_safe_join(self.root.resolve(), "../secret.txt"))
