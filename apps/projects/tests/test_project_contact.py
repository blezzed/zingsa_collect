import copy
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.forms.models import Form, FormVersion
from apps.forms.services.form_services import publish_form_service
from apps.organizations.models import Organization
from apps.projects.models import Project, ProjectMember

User = get_user_model()

CONTACT = {
    "contact_name": "Ada Maker",
    "contact_phone": "+27 82 123 4567",
    "contact_email": "ada@example.com",
    "contact_note": "WhatsApp only, weekdays 8 to 5",
}

CONTACT_BLOCK = {
    "name": "Ada Maker",
    "phone": "+27 82 123 4567",
    "email": "ada@example.com",
    "note": "WhatsApp only, weekdays 8 to 5",
}


class ProjectContactTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="thandi",
            email="thandi@example.com",
            password="pass12345",
            first_name="Thandi",
            last_name="Ncube",
        )
        self.collector = User.objects.create_user(
            username="collector",
            email="collector@example.com",
            password="pass12345",
        )
        self.org = Organization.objects.create(name="Org", code="org-contact")
        self.project = Project.objects.create(
            name="Contact Project",
            code="proj-contact",
            organization=self.org,
            owner=self.owner,
            status="active",
        )
        ProjectMember.objects.create(
            project=self.project, user=self.collector, role="collector"
        )
        self.form = self._add_form("survey", "Survey")
        self.project_url = reverse("projects:detail", kwargs={"pk": self.project.id})
        self.form_list_url = reverse(
            "projects:form_list_create",
            kwargs={"project_id": self.project.id},
        )

    def _as(self, user):
        self.client.force_authenticate(user=user)
        return self.client

    def _patch(self, payload, user=None):
        return self._as(user or self.owner).patch(
            self.project_url, payload, format="json"
        )

    def _add_form(self, slug, title):
        form = Form.objects.create(
            project=self.project,
            title=title,
            slug=slug,
            created_by=self.owner,
            status="draft",
            geometry_type="none",
            is_demo=True,
        )
        schema = {
            "formId": str(form.id),
            "title": title,
            "version": "1.0",
            "mode": "form_first",
            "projectId": self.project.code,
            "geometryType": "none",
            "questions": [
                {"id": "q1", "type": "text", "label": "Name", "required": False}
            ],
        }
        version = FormVersion.objects.create(
            form=form,
            version_number=1,
            version_label="1.0",
            schema=schema,
            checksum=f"contact-checksum-{slug}",
            is_published=False,
            column_mapping={"q1": "q1"},
            created_by=self.owner,
        )
        form.current_version = version
        form.save(update_fields=["current_version"])
        return form

    def _publish(self, form):
        with patch(
            "apps.forms.services.form_services.migrate_submissions_between_tables"
        ), patch(
            "apps.forms.services.form_services.ensure_physical_columns_service"
        ), patch(
            "apps.forms.services.form_services.create_physical_form_table_service"
        ):
            return publish_form_service(form, created_by=self.owner)

    def _contact_rows(self, response):
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        return list(response.data)

    def test_save_and_read_each_contact_field(self):
        phone = self._patch({"contact_phone": "  +27 82 123 4567  "})
        self.assertEqual(phone.status_code, status.HTTP_200_OK, phone.data)
        self.assertEqual(phone.data["contact_phone"], "+27 82 123 4567")
        self.assertEqual(phone.data["contact_name"], "")
        self.assertEqual(phone.data["contact_email"], "")
        self.assertEqual(phone.data["contact_note"], "")

        email = self._patch({"contact_email": "  ada@example.com  "})
        self.assertEqual(email.status_code, status.HTTP_200_OK, email.data)
        self.assertEqual(email.data["contact_email"], "ada@example.com")
        self.assertEqual(email.data["contact_phone"], "+27 82 123 4567")

        named = self._patch(
            {
                "contact_name": "  Ada Maker  ",
                "contact_note": "  WhatsApp only, weekdays 8 to 5  ",
            }
        )
        self.assertEqual(named.status_code, status.HTTP_200_OK, named.data)
        self.assertEqual(named.data["contact_name"], CONTACT["contact_name"])
        self.assertEqual(named.data["contact_note"], CONTACT["contact_note"])

        detail = self._as(self.owner).get(self.project_url)
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        for field, value in CONTACT.items():
            self.assertEqual(detail.data[field], value)

        form_detail = self._as(self.owner).get(
            reverse("forms:detail", kwargs={"pk": self.form.id})
        )
        self.assertEqual(form_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(form_detail.data["contact"], CONTACT_BLOCK)
        self.assertNotIn("contact_name", form_detail.data)

        listed = self._as(self.owner).get(self.form_list_url)
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        row = next(item for item in listed.data if item["id"] == str(self.form.id))
        self.assertEqual(row["contact"], CONTACT_BLOCK)

    def test_accepts_phone_length_bounds_and_brackets(self):
        for phone in ("1234567", "123456789012345", "+27 (82) 123-4567"):
            with self.subTest(phone=phone):
                response = self._patch(
                    {
                        "contact_name": "",
                        "contact_phone": phone,
                        "contact_email": "",
                        "contact_note": "",
                    }
                )
                self.assertEqual(
                    response.status_code, status.HTTP_200_OK, response.data
                )
                self.assertEqual(response.data["contact_phone"], phone)

    def test_rejects_bad_phone(self):
        for phone in (
            "12345",
            "1234567890123456",
            "082.123.4567",
            "call me",
            "++27821234567",
        ):
            with self.subTest(phone=phone):
                response = self._patch({"contact_phone": phone})
                self.assertEqual(
                    response.status_code, status.HTTP_400_BAD_REQUEST, response.data
                )
                self.assertIn("contact_phone", response.data)
                self.project.refresh_from_db()
                self.assertEqual(self.project.contact_phone, "")

    def test_rejects_bad_email(self):
        response = self._patch({"contact_email": "not-an-email"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("contact_email", response.data)
        self.project.refresh_from_db()
        self.assertEqual(self.project.contact_email, "")

    def test_refuses_name_or_note_without_a_way_to_reach_them(self):
        for payload in (
            {"contact_name": "Ada"},
            {"contact_note": "Weekdays 8 to 5"},
        ):
            with self.subTest(payload=payload):
                response = self._patch(payload)
                self.assertEqual(
                    response.status_code, status.HTTP_400_BAD_REQUEST, response.data
                )
                self.assertIn("non_field_errors", response.data)
                self.project.refresh_from_db()
                self.assertEqual(self.project.contact_name, "")
                self.assertEqual(self.project.contact_note, "")

    def test_refuses_partial_update_that_leaves_a_name_unreachable(self):
        saved = self._patch(
            {"contact_name": "Ada", "contact_phone": "+27 82 123 4567"}
        )
        self.assertEqual(saved.status_code, status.HTTP_200_OK, saved.data)

        refused = self._patch({"contact_phone": ""})
        self.assertEqual(
            refused.status_code, status.HTTP_400_BAD_REQUEST, refused.data
        )
        self.assertIn("non_field_errors", refused.data)
        self.project.refresh_from_db()
        self.assertEqual(self.project.contact_name, "Ada")
        self.assertEqual(self.project.contact_phone, "+27 82 123 4567")
        self.assertEqual(self.project.contact_email, "")

    def test_partial_clear_keeps_the_remaining_email(self):
        saved = self._patch(
            {
                "contact_name": "Ada",
                "contact_phone": "+27 82 123 4567",
                "contact_email": "ada@example.com",
            }
        )
        self.assertEqual(saved.status_code, status.HTTP_200_OK, saved.data)

        cleared_phone = self._patch({"contact_phone": ""})
        self.assertEqual(
            cleared_phone.status_code, status.HTTP_200_OK, cleared_phone.data
        )
        self.assertEqual(cleared_phone.data["contact_phone"], "")
        self.assertEqual(cleared_phone.data["contact_email"], "ada@example.com")
        self.assertEqual(cleared_phone.data["contact_name"], "Ada")

    def test_all_blank_clears_the_contact(self):
        saved = self._patch(CONTACT)
        self.assertEqual(saved.status_code, status.HTTP_200_OK, saved.data)

        cleared = self._patch(
            {
                "contact_name": "  ",
                "contact_phone": " ",
                "contact_email": " ",
                "contact_note": "  ",
            }
        )
        self.assertEqual(cleared.status_code, status.HTTP_200_OK, cleared.data)
        for field in CONTACT:
            self.assertEqual(cleared.data[field], "")
        self.project.refresh_from_db()
        self.assertEqual(self.project.contact_name, "")
        self.assertEqual(self.project.contact_phone, "")
        self.assertEqual(self.project.contact_email, "")
        self.assertEqual(self.project.contact_note, "")

    def test_collector_cannot_change_contact(self):
        saved = self._patch(CONTACT)
        self.assertEqual(saved.status_code, status.HTTP_200_OK, saved.data)

        refused = self._patch(
            {"contact_phone": "+27 11 555 0101"}, user=self.collector
        )
        self.assertEqual(refused.status_code, status.HTTP_403_FORBIDDEN)
        self.project.refresh_from_db()
        self.assertEqual(self.project.contact_phone, CONTACT["contact_phone"])

    def test_contact_suggestion_for_owner_and_null_for_collector(self):
        saved = self._patch(CONTACT)
        self.assertEqual(saved.status_code, status.HTTP_200_OK, saved.data)

        owner = self._as(self.owner).get(self.project_url)
        self.assertEqual(owner.status_code, status.HTTP_200_OK)
        self.assertEqual(
            owner.data["contact_suggestion"],
            {"name": "Thandi Ncube", "email": "thandi@example.com"},
        )
        self.assertEqual(owner.data["contact_phone"], CONTACT["contact_phone"])

        collector = self._as(self.collector).get(self.project_url)
        self.assertEqual(collector.status_code, status.HTTP_200_OK)
        self.assertIsNone(collector.data["contact_suggestion"])
        self.assertEqual(collector.data["contact_phone"], CONTACT["contact_phone"])

        self.owner.first_name = ""
        self.owner.last_name = ""
        self.owner.save(update_fields=["first_name", "last_name"])
        fallback = self._as(self.owner).get(self.project_url)
        self.assertEqual(
            fallback.data["contact_suggestion"],
            {"name": "thandi", "email": "thandi@example.com"},
        )

    def test_new_project_contact_is_blank(self):
        created = self._as(self.owner).post(
            reverse("projects:list_create"),
            {
                "name": "Fresh project",
                "contact_name": "Thandi Ncube",
                "contact_phone": "+27 82 123 4567",
                "contact_email": "thandi@example.com",
                "contact_note": "do not copy",
            },
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)
        for field in CONTACT:
            self.assertEqual(created.data[field], "")
        self.assertNotEqual(created.data["contact_name"], "Thandi Ncube")
        self.assertNotEqual(created.data["contact_email"], "thandi@example.com")
        self.assertEqual(
            created.data["contact_suggestion"],
            {"name": "Thandi Ncube", "email": "thandi@example.com"},
        )

        project = Project.objects.get(id=created.data["id"])
        self.assertEqual(project.owner_id, self.owner.id)
        self.assertEqual(project.contact_name, "")
        self.assertEqual(project.contact_phone, "")
        self.assertEqual(project.contact_email, "")
        self.assertEqual(project.contact_note, "")

    def test_logged_in_collector_sees_project_contact_on_every_form(self):
        second = self._add_form("survey-b", "Survey B")
        self._publish(self.form)
        self._publish(second)
        saved = self._patch(CONTACT)
        self.assertEqual(saved.status_code, status.HTTP_200_OK, saved.data)

        client = self._as(self.collector)
        available = self._contact_rows(client.get(reverse("forms:available")))
        rows = {
            row["id"]: row
            for row in available
            if row["id"] in {str(self.form.id), str(second.id)}
        }
        self.assertEqual(set(rows), {str(self.form.id), str(second.id)})
        for row in rows.values():
            self.assertEqual(row["contact"], CONTACT_BLOCK)

        for form in (self.form, second):
            download = client.get(reverse("forms:download", kwargs={"pk": form.id}))
            self.assertEqual(download.status_code, status.HTTP_200_OK, download.data)
            self.assertEqual(download.data["contact"], CONTACT_BLOCK)

    def test_anonymous_demo_hides_contact_on_available_and_download(self):
        second = self._add_form("survey-b", "Survey B")
        self._publish(self.form)
        self._publish(second)
        saved = self._patch(CONTACT)
        self.assertEqual(saved.status_code, status.HTTP_200_OK, saved.data)

        anon = self._as(None)
        available = self._contact_rows(anon.get(reverse("forms:available")))
        rows = [
            row
            for row in available
            if row["id"] in {str(self.form.id), str(second.id)}
        ]
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertIn("contact", row)
            self.assertIsNone(row["contact"])

        for form in (self.form, second):
            download = anon.get(reverse("forms:download", kwargs={"pk": form.id}))
            self.assertEqual(download.status_code, status.HTTP_200_OK, download.data)
            self.assertIsNone(download.data["contact"])

        self.project.refresh_from_db()
        self.assertEqual(self.project.contact_phone, CONTACT["contact_phone"])

    def test_contact_is_null_when_unset(self):
        self._publish(self.form)
        client = self._as(self.collector)

        detail = client.get(reverse("forms:detail", kwargs={"pk": self.form.id}))
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertIsNone(detail.data["contact"])

        listed = client.get(self.form_list_url)
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        row = next(item for item in listed.data if item["id"] == str(self.form.id))
        self.assertIsNone(row["contact"])

        available = self._contact_rows(client.get(reverse("forms:available")))
        available_row = next(
            item for item in available if item["id"] == str(self.form.id)
        )
        self.assertIsNone(available_row["contact"])

        download = client.get(reverse("forms:download", kwargs={"pk": self.form.id}))
        self.assertEqual(download.status_code, status.HTTP_200_OK)
        self.assertIsNone(download.data["contact"])

    def test_saving_contact_does_not_create_a_version(self):
        self._publish(self.form)
        self.form.refresh_from_db()
        version = self.form.current_version
        version_id = version.id
        checksum = version.checksum
        schema_before = copy.deepcopy(version.schema)
        version_count = self.form.versions.count()

        owner = self._as(self.owner)
        before = owner.get(reverse("forms:detail", kwargs={"pk": self.form.id}))
        self.assertEqual(before.data["status"], "published")
        self.assertFalse(before.data["force_update"])

        available = self._contact_rows(owner.get(reverse("forms:available")))
        row = next(item for item in available if item["id"] == str(self.form.id))
        self.assertTrue(row["force_update"])
        self.assertEqual(row["published_checksum"], checksum)
        self.assertIsNone(row["contact"])

        download = owner.get(reverse("forms:download", kwargs={"pk": self.form.id}))
        self.assertEqual(download.status_code, status.HTTP_200_OK)
        self.assertEqual(download.data["checksum"], checksum)
        self.assertTrue(download.data["force_update"])
        self.assertIsNone(download.data["contact"])

        saved = self._patch(CONTACT)
        self.assertEqual(saved.status_code, status.HTTP_200_OK, saved.data)
        self.assertEqual(saved.data["contact_name"], CONTACT["contact_name"])

        self.form.refresh_from_db()
        self.form.current_version.refresh_from_db()
        self.assertEqual(self.form.versions.count(), version_count)
        self.assertEqual(self.form.current_version_id, version_id)
        self.assertTrue(self.form.current_version.is_published)
        self.assertEqual(self.form.current_version.checksum, checksum)
        self.assertEqual(self.form.current_version.schema, schema_before)
        self.assertNotIn("contact", self.form.current_version.schema)
        self.assertEqual(self.form.status, "published")

        detail = owner.get(reverse("forms:detail", kwargs={"pk": self.form.id}))
        self.assertEqual(detail.data["status"], "published")
        self.assertFalse(detail.data["force_update"])
        self.assertEqual(detail.data["contact"], CONTACT_BLOCK)

        download = owner.get(reverse("forms:download", kwargs={"pk": self.form.id}))
        self.assertEqual(download.data["checksum"], checksum)
        self.assertTrue(download.data["force_update"])
        self.assertEqual(download.data["contact"], CONTACT_BLOCK)

        available = self._contact_rows(owner.get(reverse("forms:available")))
        row = next(item for item in available if item["id"] == str(self.form.id))
        self.assertTrue(row["force_update"])
        self.assertEqual(row["published_checksum"], checksum)
        self.assertEqual(row["contact"], CONTACT_BLOCK)

    def test_form_has_no_contact_fields(self):
        names = {field.name for field in Form._meta.local_fields}
        self.assertFalse(names & set(CONTACT))

    def test_project_form_list_query_count_does_not_grow_with_forms(self):
        saved = self._patch(CONTACT)
        self.assertEqual(saved.status_code, status.HTTP_200_OK, saved.data)
        self._as(self.owner)

        with CaptureQueriesContext(connection) as first:
            one = self.client.get(self.form_list_url)
        self.assertEqual(one.status_code, status.HTTP_200_OK, one.data)
        self.assertEqual(len(one.data), 1)
        self.assertEqual(one.data[0]["contact"], CONTACT_BLOCK)

        self._add_form("survey-b", "Survey B")
        self._add_form("survey-c", "Survey C")

        with CaptureQueriesContext(connection) as second:
            many = self.client.get(self.form_list_url)
        self.assertEqual(many.status_code, status.HTTP_200_OK, many.data)
        self.assertEqual(len(many.data), 3)
        for row in many.data:
            self.assertEqual(row["contact"], CONTACT_BLOCK)
        self.assertGreater(len(first), 0)
        self.assertEqual(len(second), len(first))
