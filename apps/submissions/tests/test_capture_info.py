import csv
import json
import zipfile
from io import BytesIO, StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.forms.models import Form, FormVersion
from apps.forms.services.form_services import (
    calculate_form_checksum_service,
    create_physical_form_table_service,
    generate_column_mapping_service,
    generate_form_table_name_service,
    publish_form_service,
    update_form_service,
)
from apps.projects.models import Project
from apps.submissions.models import SubmissionIndex
from apps.submissions.services.capture_info import sanitize_capture_info

User = get_user_model()

POINT = {"type": "Point", "coordinates": [31.05, -17.82]}

SAMPLE_SITE = {
    "accuracy_m": 8.5,
    "altitude_m": 1420.2,
    "provider": "gps",
    "captured_at": "2026-11-04T10:15:00Z",
    "mock_location": False,
}

TWO_READINGS = {
    "gps": {
        "site_location": dict(SAMPLE_SITE),
        "route_line": {
            "accuracy_m": 22.0,
            "altitude_m": 1400.0,
            "provider": "gps",
            "captured_at": "2026-11-04T10:16:00Z",
            "mock_location": False,
        },
    },
    "device": {
        "platform": "android",
        "os_version": "14",
        "manufacturer": "Samsung",
        "model": "SM-A156E",
        "app_version": "1.4.0",
    },
}


class CaptureInfoTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="captureuser", password="password123")
        self.client.force_authenticate(user=self.user)
        self.project = Project.objects.create(
            name="Capture Project", code="CAP-1", owner=self.user
        )
        self.form, self.version = self._publish_form(
            slug="capture-form",
            title="Capture Form",
            questions=[
                {"id": "location_name", "type": "text", "label": "Name"},
                {"id": "geom_point", "type": "point", "label": "Location"},
            ],
        )

    def _publish_form(self, slug, title, questions, geometry_type="point"):
        form = Form.objects.create(
            project=self.project,
            title=title,
            slug=slug,
            status="draft",
            geometry_type=geometry_type,
            created_by=self.user,
        )
        schema = {
            "formId": str(form.id),
            "title": title,
            "version": "1.0",
            "mode": "map_first",
            "geometryType": geometry_type,
            "projectId": self.project.code,
            "questions": questions,
        }
        mapping, _ = generate_column_mapping_service(schema["questions"])
        version = FormVersion.objects.create(
            form=form,
            version_number=1,
            version_label="1.0",
            schema=schema,
            checksum=calculate_form_checksum_service(schema),
            column_mapping=mapping,
            created_by=self.user,
            is_published=True,
        )
        version.physical_table_name = generate_form_table_name_service(
            form.slug, 1, form.id
        )
        version.save()
        create_physical_form_table_service(version)
        form.status = "published"
        form.current_version = version
        form.submission_table_name = version.physical_table_name
        form.save()
        return form, version

    def _answers(self, name):
        return {
            "location_name": name,
            "geom_point": POINT,
        }

    def _sync(self, client_id, capture_info=None, include_capture=True, answers=None, version=None):
        version = version or self.version
        body = {
            "device_id": "device-1",
            "client_submission_id": client_id,
            "form_version_id": str(version.id),
            "answers": answers if answers is not None else self._answers(client_id),
        }
        if include_capture:
            body["capture_info"] = capture_info
        return self.client.post(reverse("sync:single_sync"), body, format="json")

    def _index(self, client_id):
        return SubmissionIndex.objects.get(
            form=self.form,
            device_id="device-1",
            client_submission_id=client_id,
        )

    def test_single_and_bulk_sync_save_capture_info_and_largest_accuracy(self):
        single = self._sync("local-100", TWO_READINGS)
        self.assertEqual(single.status_code, status.HTTP_201_CREATED)
        self.assertFalse(single.data["is_duplicate"])
        self.assertEqual(single.data["submission"]["gps_accuracy_m"], 22.0)

        stored = single.data["submission"]["capture_info"]
        site = stored["gps"]["site_location"]
        self.assertEqual(site["accuracy_m"], 8.5)
        self.assertAlmostEqual(site["altitude_m"], 1420.2)
        self.assertEqual(site["provider"], "gps")
        self.assertEqual(site["captured_at"], "2026-11-04T10:15:00Z")
        self.assertIs(site["mock_location"], False)
        self.assertEqual(stored["gps"]["route_line"]["accuracy_m"], 22.0)
        self.assertEqual(stored["device"], TWO_READINGS["device"])
        self.assertEqual(self._index("local-100").gps_accuracy_m, 22.0)

        bulk = self.client.post(
            reverse("sync:bulk_sync"),
            {
                "device_id": "device-1",
                "submissions": [
                    {
                        "client_submission_id": "local-bulk",
                        "form_version_id": str(self.version.id),
                        "answers": self._answers("bulk"),
                        "capture_info": TWO_READINGS,
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(bulk.status_code, status.HTTP_200_OK)
        self.assertEqual(bulk.data["total_success"], 1)
        self.assertEqual(bulk.data["total_failed"], 0)
        bulk_index = self._index("local-bulk")
        self.assertEqual(bulk_index.gps_accuracy_m, 22.0)
        self.assertEqual(bulk_index.capture_info["device"]["app_version"], "1.4.0")
        self.assertEqual(bulk_index.capture_info["gps"]["site_location"]["accuracy_m"], 8.5)

    def test_missing_capture_info_saves_empty_object_and_null_accuracy(self):
        response = self._sync("local-plain", include_capture=False)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        index = self._index("local-plain")
        self.assertEqual(index.capture_info, {})
        self.assertIsNone(index.gps_accuracy_m)
        detail = self.client.get(
            reverse(
                "web_data:data_detail",
                kwargs={"form_id": self.form.id, "row_id": index.physical_row_id},
            )
        )
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.json()["answers"]["location_name"], "local-plain")

    def test_malformed_capture_info_still_saves_the_submission(self):
        for client_id, raw in (
            ("local-string", "not-an-object"),
            ("local-list", ["gps"]),
            ("local-number", 8.5),
        ):
            response = self._sync(client_id, raw)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED, client_id)
            index = self._index(client_id)
            self.assertEqual(index.capture_info, {})
            self.assertIsNone(index.gps_accuracy_m)
            self.assertEqual(index.client_submission_id, client_id)

    def test_unknown_keys_are_dropped_at_each_level(self):
        response = self._sync(
            "local-unknown",
            {
                "owner_name": "Ada",
                "advertising_id": "ad-1",
                "gps": {
                    "site_location": {
                        "accuracy_m": 4,
                        "provider": "  gps  ",
                        "imei": "should-drop",
                        "serial": "abc",
                    }
                },
                "device": {
                    "platform": "android",
                    "imei": "356938035643809",
                    "os_version": "  14  ",
                },
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        stored = self._index("local-unknown").capture_info
        self.assertEqual(
            stored,
            {
                "gps": {"site_location": {"accuracy_m": 4, "provider": "gps"}},
                "device": {"platform": "android", "os_version": "14"},
            },
        )
        dumped = json.dumps(stored)
        self.assertNotIn("imei", dumped)
        self.assertNotIn("owner_name", dumped)
        self.assertNotIn("advertising_id", dumped)
        self.assertNotIn("serial", dumped)

    def test_invalid_accuracy_is_dropped_and_the_rest_of_the_entry_stays(self):
        capture = {
            "gps": {
                "negative": {
                    "accuracy_m": -1,
                    "provider": "gps",
                    "altitude_m": 10,
                    "captured_at": "2026-11-04T10:15:00Z",
                    "mock_location": False,
                },
                "text": {
                    "accuracy_m": "8.5",
                    "provider": "network",
                    "altitude_m": 11,
                    "captured_at": "2026-11-04T10:15:00Z",
                    "mock_location": True,
                },
                "bool_value": {
                    "accuracy_m": True,
                    "provider": "gps",
                    "altitude_m": 12,
                    "captured_at": "2026-11-04T10:15:00Z",
                    "mock_location": False,
                },
                "infinite": {
                    "accuracy_m": "INF_PLACEHOLDER",
                    "provider": "gps",
                    "altitude_m": 13,
                    "captured_at": "2026-11-04T10:15:00Z",
                    "mock_location": False,
                },
            },
            "device": {"platform": "android", "model": "SM-A156E"},
        }
        body = json.dumps({
            "device_id": "device-1",
            "client_submission_id": "local-bad-accuracy",
            "form_version_id": str(self.version.id),
            "answers": self._answers("bad-accuracy"),
            "capture_info": capture,
        }).replace('"INF_PLACEHOLDER"', "1e999")
        response = self.client.post(
            reverse("sync:single_sync"),
            data=body,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        index = self._index("local-bad-accuracy")
        self.assertIsNone(index.gps_accuracy_m)
        gps = index.capture_info["gps"]
        self.assertEqual(set(gps), {"negative", "text", "bool_value", "infinite"})
        for reading in gps.values():
            self.assertNotIn("accuracy_m", reading)
            self.assertIn("provider", reading)
            self.assertIn("altitude_m", reading)
            self.assertIn("captured_at", reading)
            self.assertIn("mock_location", reading)
        self.assertEqual(gps["text"]["provider"], "network")
        self.assertIs(gps["text"]["mock_location"], True)
        self.assertEqual(gps["negative"]["altitude_m"], 10)

    def test_long_strings_are_dropped_and_gps_entries_are_limited(self):
        long_id = "q" * 101
        response = self._sync(
            "local-long",
            {
                "gps": {
                    "ok": {
                        "accuracy_m": 5,
                        "provider": "p" * 101,
                        "altitude_m": 1,
                    },
                    long_id: {"accuracy_m": 6, "provider": "gps"},
                },
                "device": {
                    "manufacturer": "M" * 101,
                    "model": "S" * 100,
                    "app_version": "1",
                },
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        stored = self._index("local-long").capture_info
        self.assertEqual(set(stored["gps"]), {"ok"})
        self.assertNotIn("provider", stored["gps"]["ok"])
        self.assertEqual(stored["gps"]["ok"]["accuracy_m"], 5)
        self.assertNotIn("manufacturer", stored["device"])
        self.assertEqual(stored["device"]["model"], "S" * 100)
        self.assertEqual(stored["device"]["app_version"], "1")

        many = {
            f"g{i:02d}": {"accuracy_m": i, "provider": "gps"}
            for i in range(51)
        }
        limited = self._sync("local-many", {"gps": many})
        self.assertEqual(limited.status_code, status.HTTP_201_CREATED)
        gps = self._index("local-many").capture_info["gps"]
        self.assertEqual(len(gps), 50)
        self.assertIn("g00", gps)
        self.assertIn("g49", gps)
        self.assertNotIn("g50", gps)
        self.assertEqual(self._index("local-many").gps_accuracy_m, 49.0)

    def test_retry_does_not_change_stored_capture_info(self):
        first = self._sync("local-retry", TWO_READINGS)
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        original_id = first.data["submission"]["id"]

        replacement = {
            "gps": {"site_location": {"accuracy_m": 1, "provider": "gps"}},
            "device": {"app_version": "9.9.9", "model": "Other"},
        }
        second = self._sync("local-retry", replacement)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertTrue(second.data["is_duplicate"])
        self.assertEqual(second.data["submission"]["id"], original_id)
        self.assertEqual(second.data["submission"]["gps_accuracy_m"], 22.0)
        self.assertEqual(
            second.data["submission"]["capture_info"]["device"]["app_version"],
            "1.4.0",
        )
        index = self._index("local-retry")
        self.assertEqual(str(index.id), original_id)
        self.assertEqual(index.capture_info["device"]["model"], "SM-A156E")
        self.assertEqual(index.gps_accuracy_m, 22.0)

    def test_row_detail_returns_capture_info_and_accuracy(self):
        self._sync("local-detail", TWO_READINGS)
        index = self._index("local-detail")
        response = self.client.get(
            reverse(
                "web_data:data_detail",
                kwargs={"form_id": self.form.id, "row_id": index.physical_row_id},
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        metadata = response.json()["metadata"]
        self.assertEqual(metadata["gps_accuracy_m"], 22.0)
        self.assertEqual(metadata["capture_info"]["device"]["model"], "SM-A156E")
        self.assertEqual(metadata["capture_info"]["gps"]["site_location"]["accuracy_m"], 8.5)

        by_uuid = self.client.get(
            reverse("submissions:detail", kwargs={"pk": index.id})
        )
        self.assertEqual(by_uuid.status_code, status.HTTP_200_OK)
        self.assertEqual(by_uuid.json()["metadata"]["gps_accuracy_m"], 22.0)
        self.assertIn("capture_info", by_uuid.json()["metadata"])

    def test_table_and_exports_include_capture_columns(self):
        self._sync("with-capture", TWO_READINGS, answers=self._answers("With capture"))
        self._sync("without-capture", include_capture=False, answers=self._answers("Without"))

        columns = self.client.get(
            reverse("web_data:columns", kwargs={"form_id": self.form.id})
        )
        self.assertEqual(columns.status_code, status.HTTP_200_OK)
        column_ids = [column["id"] for column in columns.json()]
        self.assertIn("gps_accuracy_m", column_ids)
        self.assertIn("device_model", column_ids)
        self.assertIn("app_version", column_ids)

        table = self.client.get(
            reverse("web_data:data_paginated", kwargs={"form_id": self.form.id})
        )
        self.assertEqual(table.status_code, status.HTTP_200_OK)
        by_name = {row["location_name"]: row for row in table.json()["data"]}
        rich = by_name["With capture"]
        empty = by_name["Without"]
        self.assertEqual(rich["gps_accuracy_m"], 22.0)
        self.assertEqual(rich["device_model"], "Samsung SM-A156E")
        self.assertEqual(rich["app_version"], "1.4.0")
        self.assertEqual(empty["gps_accuracy_m"], "")
        self.assertEqual(empty["device_model"], "")
        self.assertEqual(empty["app_version"], "")

        exported = self.client.get(
            reverse("web_data:data_export", kwargs={"form_id": self.form.id}),
            {"export_format": "csv"},
        )
        self.assertEqual(exported.status_code, status.HTTP_200_OK)
        rows = list(csv.DictReader(StringIO(exported.content.decode("utf-8-sig"))))
        csv_by_name = {row["Name"]: row for row in rows}
        self.assertEqual(csv_by_name["With capture"]["GPS Accuracy (m)"], "22.0")
        self.assertEqual(csv_by_name["With capture"]["Device Model"], "Samsung SM-A156E")
        self.assertEqual(csv_by_name["With capture"]["App Version"], "1.4.0")
        self.assertEqual(csv_by_name["Without"]["GPS Accuracy (m)"], "")
        self.assertEqual(csv_by_name["Without"]["Device Model"], "")
        self.assertEqual(csv_by_name["Without"]["App Version"], "")

        json_export = self.client.get(
            reverse("web_data:data_export", kwargs={"form_id": self.form.id}),
            {"export_format": "json"},
        )
        json_rows = {
            row["location_name"]: row
            for row in json.loads(json_export.content.decode("utf-8"))["data"]
        }
        self.assertEqual(json_rows["With capture"]["device_model"], "Samsung SM-A156E")
        self.assertEqual(json_rows["Without"]["app_version"], "")

        xlsx = self.client.get(
            reverse("web_data:data_export", kwargs={"form_id": self.form.id}),
            {"export_format": "xlsx"},
        )
        with zipfile.ZipFile(BytesIO(xlsx.content)) as workbook:
            sheet = workbook.read("xl/worksheets/sheet1.xml").decode("utf-8")
        self.assertIn("GPS Accuracy (m)", sheet)
        self.assertIn("Samsung SM-A156E", sheet)
        self.assertIn("1.4.0", sheet)

        kml = self.client.get(
            reverse("web_data:data_export", kwargs={"form_id": self.form.id}),
            {"export_format": "kml"},
        )
        kml_body = kml.content.decode("utf-8")
        self.assertIn('name="gps_accuracy_m"', kml_body)
        self.assertIn('name="device_model"', kml_body)
        self.assertIn('name="app_version"', kml_body)
        self.assertIn("Samsung SM-A156E", kml_body)
        self.assertIn("1.4.0", kml_body)

    def test_question_named_gps_accuracy_m_keeps_its_answer(self):
        form, version = self._publish_form(
            slug="accuracy-question",
            title="Accuracy Question",
            questions=[
                {"id": "gps_accuracy_m", "type": "text", "label": "Survey accuracy"},
                {"id": "location_name", "type": "text", "label": "Name"},
            ],
            geometry_type="none",
        )
        response = self.client.post(
            reverse("sync:single_sync"),
            {
                "device_id": "device-1",
                "client_submission_id": "local-question",
                "form_version_id": str(version.id),
                "answers": {
                    "gps_accuracy_m": "kept-answer",
                    "location_name": "Named",
                },
                "capture_info": TWO_READINGS,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["submission"]["gps_accuracy_m"], 22.0)

        table = self.client.get(
            reverse("web_data:data_paginated", kwargs={"form_id": form.id})
        )
        row = table.json()["data"][0]
        self.assertEqual(row["gps_accuracy_m"], "kept-answer")
        self.assertEqual(row["device_model"], "Samsung SM-A156E")
        self.assertEqual(row["app_version"], "1.4.0")

        columns = self.client.get(
            reverse("web_data:columns", kwargs={"form_id": form.id})
        )
        accuracy_columns = [
            column for column in columns.json() if column["id"] == "gps_accuracy_m"
        ]
        self.assertEqual(len(accuracy_columns), 1)
        self.assertEqual(accuracy_columns[0]["label"], "Survey accuracy")

        exported = self.client.get(
            reverse("web_data:data_export", kwargs={"form_id": form.id}),
            {"export_format": "csv"},
        )
        sheet = csv.DictReader(StringIO(exported.content.decode("utf-8-sig")))
        self.assertIn("Survey accuracy", sheet.fieldnames)
        self.assertNotIn("gps_accuracy_m", sheet.fieldnames)
        self.assertEqual(next(sheet)["Survey accuracy"], "kept-answer")

    def test_table_query_count_does_not_grow_with_rows(self):
        self._sync("local-q1", TWO_READINGS)
        url = reverse("web_data:data_paginated", kwargs={"form_id": self.form.id})
        with CaptureQueriesContext(connection) as first:
            first_response = self.client.get(url)
        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(first_response.json()["data"]), 1)

        for index in range(2, 6):
            self._sync(f"local-q{index}", TWO_READINGS)

        with CaptureQueriesContext(connection) as second:
            second_response = self.client.get(url)
        self.assertEqual(len(second_response.json()["data"]), 5)
        self.assertEqual(
            len(first),
            len(second),
            f"table queries grew from {len(first)} with 1 row to {len(second)} with 5 rows",
        )

    def test_capture_info_stays_on_the_same_index_when_rows_move(self):
        self._sync("local-move", TWO_READINGS, answers=self._answers("Moved"))
        index = self._index("local-move")
        original_pk = index.id

        schema_v2 = dict(self.version.schema)
        schema_v2["questions"] = list(schema_v2["questions"]) + [
            {"id": "q_notes", "type": "text", "label": "Notes"},
        ]
        update_form_service(self.form, {}, schema=schema_v2, user=self.user)
        self.form.refresh_from_db()
        publish_form_service(self.form, created_by=self.user)
        self.form.refresh_from_db()

        table = self.client.get(
            reverse("web_data:data_paginated", kwargs={"form_id": self.form.id})
        )
        self.assertEqual(table.status_code, status.HTTP_200_OK)
        row = next(item for item in table.json()["data"] if item["location_name"] == "Moved")
        self.assertEqual(row["device_model"], "Samsung SM-A156E")
        self.assertEqual(row["gps_accuracy_m"], 22.0)

        index.refresh_from_db()
        self.assertEqual(index.id, original_pk)
        self.assertEqual(
            SubmissionIndex.objects.filter(client_submission_id="local-move").count(),
            1,
        )
        self.assertEqual(index.physical_table_name, self.form.submission_table_name)
        self.assertEqual(index.physical_row_id, row["id"])
        self.assertEqual(index.capture_info["device"]["app_version"], "1.4.0")
        self.assertEqual(index.gps_accuracy_m, 22.0)

    def test_unexpected_capture_error_still_saves_the_submission(self):
        with patch(
            "apps.submissions.services.capture_info.sanitize_capture_info",
            side_effect=RuntimeError("capture parser failed"),
        ):
            response = self._sync("local-boom", TWO_READINGS)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        index = self._index("local-boom")
        self.assertEqual(index.capture_info, {})
        self.assertIsNone(index.gps_accuracy_m)

        real_create = SubmissionIndex.objects.create

        def reject_capture(*args, **kwargs):
            if kwargs.get("capture_info"):
                raise RuntimeError("capture_info rejected")
            return real_create(*args, **kwargs)

        with patch(
            "apps.submissions.services.capture_info.SubmissionIndex.objects.create",
            side_effect=reject_capture,
        ):
            saved = self._sync("local-db", TWO_READINGS, answers=self._answers("Kept answer"))
        self.assertEqual(saved.status_code, status.HTTP_201_CREATED)
        index = self._index("local-db")
        self.assertEqual(index.capture_info, {})
        self.assertIsNone(index.gps_accuracy_m)
        detail = self.client.get(
            reverse(
                "web_data:data_detail",
                kwargs={"form_id": self.form.id, "row_id": index.physical_row_id},
            )
        )
        self.assertEqual(detail.json()["answers"]["location_name"], "Kept answer")

    def test_sanitize_drops_non_finite_numbers(self):
        stored, accuracy = sanitize_capture_info({
            "gps": {
                "site_location": {
                    "accuracy_m": float("nan"),
                    "altitude_m": float("inf"),
                    "provider": "gps",
                }
            }
        })
        self.assertEqual(stored, {"gps": {"site_location": {"provider": "gps"}}})
        self.assertIsNone(accuracy)
