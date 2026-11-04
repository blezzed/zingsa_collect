import copy
import csv
import json
import zipfile
from datetime import date
from io import BytesIO, StringIO

from django.db import DataError, connection
from django.urls import reverse
from django.contrib.auth import get_user_model
from psycopg2 import sql
from rest_framework import status
from rest_framework.test import APITestCase

from apps.forms.models import Form, FormVersion
from apps.projects.models import Project
from apps.submissions.services.submission_services import sync_submission_to_physical_table_service
from apps.forms.services.form_services import generate_column_mapping_service, calculate_form_checksum_service, generate_form_table_name_service, create_physical_form_table_service

User = get_user_model()

class WebDataViewsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='webuser', password='password123')
        self.client.force_authenticate(user=self.user)

        self.project = Project.objects.create(name='Web Project', code='WEB-1', owner=self.user)
        self.form = Form.objects.create(
            project=self.project,
            title='Geo Form',
            slug='geo-form',
            status='draft',
            geometry_type='point',
            created_by=self.user
        )
        schema = {
            'formId': str(self.form.id),
            'title': 'Geo Form',
            'version': '1.0',
            'mode': 'map_first',
            'geometryType': 'point',
            'projectId': 'WEB-1',
            'questions': [
                {'id': 'location_name', 'type': 'text', 'label': 'Name'},
                {'id': 'geom_point', 'type': 'point', 'label': 'Location Point'},
                {'id': 'geom_generic', 'type': 'geometry', 'label': 'Shape'},
            ]
        }
        mapping, _ = generate_column_mapping_service(schema['questions'])
        
        self.version = FormVersion.objects.create(
            form=self.form,
            version_number=1,
            version_label="1.0",
            schema=schema,
            checksum=calculate_form_checksum_service(schema),
            column_mapping=mapping,
            created_by=self.user,
            is_published=True
        )
        self.version.physical_table_name = generate_form_table_name_service(self.form.slug, 1, self.form.id)
        self.version.save()
        create_physical_form_table_service(self.version)
        self.form.status = 'published'
        self.form.current_version = self.version
        self.form.submission_table_name = self.version.physical_table_name
        self.form.save()

        # Seed 5 records
        for i in range(1, 6):
            sync_submission_to_physical_table_service(
                client_submission_id=f'sub-{i}',
                device_id='device-1',
                form_version=self.version,
                answers={
                    'location_name': f'Point {i}',
                    'geom_point': {'type': 'Point', 'coordinates': [31.0 + i, -17.0 - i]},
                    'geom_generic': {'type': 'Point', 'coordinates': [31.0 + i, -17.0 - i]},
                },
                user=self.user
            )

    def test_geojson_endpoint(self):
        url = reverse('web_data:geojson', kwargs={'form_id': self.form.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['type'], 'FeatureCollection')
        self.assertEqual(len(data['features']), 10)
        self.assertEqual(data['features'][0]['type'], 'Feature')
        self.assertIn('geometry', data['features'][0])
        self.assertEqual(data['features'][0]['geometry']['type'], 'Point')
        self.assertIn('id', data['features'][0]['properties'])
        self.assertEqual(data['features'][0]['properties']['location_name'], 'Point 1')
        self.assertEqual(data['features'][0]['properties']['submitted_by'], 'webuser')
        self.assertTrue(
            data['features'][0]['properties']['geom_point'].startswith('POINT')
        )
        self.assertEqual(data['features'][1]['geometry']['type'], 'Point')
        self.assertEqual(
            data['features'][1]['properties']['geom_generic']['type'], 'Point'
        )

    def test_generic_geometry_keeps_line_and_polygon(self):
        line_points = [
            {"latitude": -17.2, "longitude": 31.2},
            {"latitude": -17.3, "longitude": 31.3},
            {"latitude": -17.4, "longitude": 31.4},
        ]
        polygon_points = [
            {"latitude": -17.5, "longitude": 31.5},
            {"latitude": -17.6, "longitude": 31.6},
            {"latitude": -17.55, "longitude": 31.7},
        ]
        sync_submission_to_physical_table_service(
            client_submission_id="sub-line",
            device_id="device-1",
            form_version=self.version,
            answers={
                "location_name": "Line capture",
                "geom_point": {"type": "Point", "coordinates": [31.2, -17.2]},
                "geom_generic": {
                    "type": "line",
                    "latitude": -17.2,
                    "longitude": 31.2,
                    "points": line_points,
                },
            },
            user=self.user,
        )
        sync_submission_to_physical_table_service(
            client_submission_id="sub-polygon",
            device_id="device-1",
            form_version=self.version,
            answers={
                "location_name": "Polygon capture",
                "geom_point": {"type": "Point", "coordinates": [31.5, -17.5]},
                "geom_generic": {
                    "type": "polygon",
                    "latitude": -17.5,
                    "longitude": 31.5,
                    "points": polygon_points,
                },
            },
            user=self.user,
        )

        url = reverse("web_data:geojson", kwargs={"form_id": self.form.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        features = response.json()["features"]

        def generic_type(name):
            matches = [
                feature
                for feature in features
                if feature["properties"].get("location_name") == name
                and feature["properties"].get("question_type") == "geometry"
            ]
            self.assertEqual(len(matches), 1)
            return matches[0]["geometry"]["type"]

        self.assertEqual(generic_type("Line capture"), "LineString")
        self.assertEqual(generic_type("Polygon capture"), "Polygon")

    def test_csv_export_includes_spatial_answers_as_wkt(self):
        url = reverse("web_data:data_export", kwargs={"form_id": self.form.id})
        response = self.client.get(url, {"export_format": "csv"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        rows = csv.DictReader(StringIO(response.content.decode("utf-8-sig")))
        first_row = next(rows)
        self.assertIn("Location Point", rows.fieldnames)
        self.assertIn("Shape", rows.fieldnames)
        self.assertTrue(first_row["Location Point"].startswith("POINT"))
        self.assertTrue(first_row["Shape"].startswith("POINT"))

    def test_geojson_export_includes_submission_answers(self):
        url = reverse("web_data:data_export", kwargs={"form_id": self.form.id})
        response = self.client.get(url, {"export_format": "geojson"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        feature = response.json()["features"][0]
        self.assertEqual(feature["properties"]["location_name"], "Point 1")
        self.assertEqual(feature["properties"]["submitted_by"], "webuser")

    def test_kml_export(self):
        url = reverse("web_data:data_export", kwargs={"form_id": self.form.id})
        response = self.client.get(url, {"export_format": "kml"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("kml", response["Content-Type"])
        self.assertIn(".kml", response["Content-Disposition"])
        body = response.content.decode("utf-8")
        self.assertIn("<kml", body)
        self.assertIn("<Placemark>", body)
        self.assertIn("<Point>", body)
        self.assertGreaterEqual(body.count("<Placemark>"), 5)
        self.assertIn("31.0,", body)

    def test_columns_endpoint(self):
        url = reverse('web_data:columns', kwargs={'form_id': self.form.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        col_names = [col['label'] for col in data]
        self.assertIn('Name', col_names)
        self.assertNotIn('Location Point', col_names)  # spatial fields belong on the map
        self.assertIn('ID', col_names)

    def test_paginated_data_endpoint(self):
        url = reverse('web_data:data_paginated', kwargs={'form_id': self.form.id})
        response = self.client.get(f"{url}?page=1&limit=2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['total'], 5)
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['limit'], 2)
        self.assertEqual(len(data['data']), 2)
        
        # Verify geometry column is stripped from attribute data
        row = data['data'][0]
        self.assertIn('location_name', row)
        self.assertNotIn('geom_point', row)

    def test_detail_data_endpoint(self):
        # First get the paginated data to extract a physical ID
        url_paginated = reverse('web_data:data_paginated', kwargs={'form_id': self.form.id})
        res_paginated = self.client.get(url_paginated).json()
        row_id = res_paginated['data'][0]['id']
        
        url_detail = reverse('web_data:data_detail', kwargs={'form_id': self.form.id, 'row_id': row_id})
        response = self.client.get(url_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('metadata', data)
        self.assertIn('answers', data)
        self.assertIn('geom_point', data['answers']) # Detail view MUST include geometry


class PreviousVersionSubmissionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="versionuser", password="password123"
        )
        self.client.force_authenticate(user=self.user)
        self.project = Project.objects.create(
            name="Version Project", code="VER-1", owner=self.user, status="active"
        )
        self.form = Form.objects.create(
            project=self.project,
            title="Version Form",
            slug="version-form",
            status="draft",
            geometry_type="none",
            created_by=self.user,
        )
        schema = {
            "formId": str(self.form.id),
            "title": "Version Form",
            "version": "1.0",
            "mode": "form_first",
            "geometryType": "none",
            "projectId": "VER-1",
            "questions": [
                {"id": "q_name", "type": "text", "label": "Name"},
            ],
        }
        mapping, _ = generate_column_mapping_service(schema["questions"])
        self.v1 = FormVersion.objects.create(
            form=self.form,
            version_number=1,
            version_label="1.0",
            schema=schema,
            checksum=calculate_form_checksum_service(schema),
            column_mapping=mapping,
            created_by=self.user,
            is_published=False,
        )
        self.form.current_version = self.v1
        self.form.save()

    def _publish_v1(self):
        from apps.forms.services.form_services import publish_form_service

        published = publish_form_service(self.form, created_by=self.user)
        self.form.refresh_from_db()
        self.v1.refresh_from_db()
        return published

    def _publish_v2(self):
        from apps.forms.services.form_services import (
            publish_form_service,
            update_form_service,
        )

        schema_v2 = dict(self.v1.schema)
        schema_v2["questions"] = [
            {"id": "q_name", "type": "text", "label": "Name"},
            {"id": "q_notes", "type": "text", "label": "Notes"},
        ]
        update_form_service(self.form, {}, schema=schema_v2, user=self.user)
        self.form.refresh_from_db()
        v2 = publish_form_service(self.form, created_by=self.user)
        self.form.refresh_from_db()
        self.v1.refresh_from_db()
        return v2

    def test_old_version_sync_appears_in_submissions_table(self):
        self._publish_v1()
        sync_submission_to_physical_table_service(
            client_submission_id="sub-v1-a",
            device_id="device-1",
            form_version=self.v1,
            answers={"q_name": "Alice"},
            user=self.user,
        )
        self._publish_v2()
        self.assertFalse(self.v1.is_published)

        sync_submission_to_physical_table_service(
            client_submission_id="sub-v1-b",
            device_id="device-old",
            form_version=self.v1,
            answers={"q_name": "Bob on v1"},
            user=self.user,
        )

        url = reverse("web_data:data_paginated", kwargs={"form_id": self.form.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = {row.get("q_name") for row in response.json()["data"]}
        self.assertEqual(names, {"Alice", "Bob on v1"})
        self.assertEqual(response.json()["total"], 2)

    def test_rows_left_on_old_table_are_copied_into_live_grid(self):
        from unittest.mock import patch

        self._publish_v1()
        self._publish_v2()

        with patch(
            "apps.submissions.services.submission_services.get_live_submission_version",
            return_value=self.v1,
        ):
            sync_submission_to_physical_table_service(
                client_submission_id="sub-orphan",
                device_id="device-orphan",
                form_version=self.v1,
                answers={"q_name": "Orphan on v1"},
                user=self.user,
            )

        url = reverse("web_data:data_paginated", kwargs={"form_id": self.form.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = {row.get("q_name") for row in response.json()["data"]}
        self.assertIn("Orphan on v1", names)

    def test_republished_form_first_detail_reads_the_live_row(self):
        from apps.submissions.models import SubmissionIndex

        self._publish_v1()
        sync_submission_to_physical_table_service(
            client_submission_id="sub-v1-detail",
            device_id="device-detail",
            form_version=self.v1,
            answers={"q_name": "Alice"},
            user=self.user,
        )
        self._publish_v2()
        self.form.refresh_from_db()
        live_table = self.form.submission_table_name
        self.assertNotEqual(live_table, self.v1.physical_table_name)
        self.assertTrue(
            SubmissionIndex.objects.filter(
                form=self.form,
                physical_table_name=self.v1.physical_table_name,
            ).exists()
        )

        list_url = reverse("web_data:data_paginated", kwargs={"form_id": self.form.id})
        listed = self.client.get(list_url)
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        row_id = listed.json()["data"][0]["id"]

        detail_url = reverse(
            "web_data:data_detail",
            kwargs={"form_id": self.form.id, "row_id": row_id},
        )
        detail = self.client.get(detail_url)
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        body = detail.json()
        self.assertEqual(body["answers"].get("q_name"), "Alice")
        self.assertIn("q_notes", body["answers"])
        self.assertEqual(body["metadata"]["physical_table_name"], live_table)
        self.assertEqual(body["metadata"]["physical_row_id"], row_id)


class DateFormatSubmissionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="dateuser", password="password123"
        )
        self.client.force_authenticate(user=self.user)
        self.project = Project.objects.create(
            name="Date Project", code="DATE-1", owner=self.user
        )
        self.form = Form.objects.create(
            project=self.project,
            title="Date Form",
            slug="date-form",
            status="draft",
            geometry_type="point",
            created_by=self.user,
        )
        schema = {
            "formId": str(self.form.id),
            "title": "Date Form",
            "version": "1.0",
            "mode": "form_first",
            "geometryType": "point",
            "projectId": "DATE-1",
            "questions": [
                {"id": "place", "type": "text", "label": "Place"},
                {
                    "id": "event_date",
                    "type": "date",
                    "label": "Event date",
                    "dateFormat": "full_date",
                },
                {"id": "legacy_date", "type": "date", "label": "Legacy date"},
                {
                    "id": "survey_month",
                    "type": "date",
                    "label": "Survey month",
                    "dateFormat": "month_year",
                },
                {
                    "id": "survey_year",
                    "type": "date",
                    "label": "Survey year",
                    "dateFormat": "year",
                },
                {
                    "id": "visit",
                    "type": "group",
                    "label": "Visit",
                    "questions": [
                        {
                            "id": "visit_day",
                            "type": "date",
                            "label": "Visit day",
                            "dateFormat": "full_date",
                        }
                    ],
                },
                {
                    "id": "visits",
                    "type": "collection",
                    "label": "Visits",
                    "questions": [
                        {
                            "id": "visited",
                            "type": "date",
                            "label": "Visited",
                            "dateFormat": "month_year",
                        },
                        {
                            "id": "visited_on",
                            "type": "date",
                            "label": "Visited on",
                            "dateFormat": "full_date",
                        },
                    ],
                },
                {
                    "id": "loose_visits",
                    "type": "collection",
                    "label": "Loose visits",
                    "questions": [
                        {"id": "loose_when", "type": "date", "label": "Loose when"},
                    ],
                },
                {"id": "geom_point", "type": "point", "label": "Location"},
            ],
        }
        mapping, _ = generate_column_mapping_service(schema["questions"])
        self.version = FormVersion.objects.create(
            form=self.form,
            version_number=1,
            version_label="1.0",
            schema=schema,
            checksum=calculate_form_checksum_service(schema),
            column_mapping=mapping,
            created_by=self.user,
            is_published=True,
        )
        self.version.physical_table_name = generate_form_table_name_service(
            self.form.slug, 1, self.form.id
        )
        self.version.save()
        create_physical_form_table_service(self.version)
        self.form.status = "published"
        self.form.current_version = self.version
        self.form.submission_table_name = self.version.physical_table_name
        self.form.save()

        sync_submission_to_physical_table_service(
            client_submission_id="sub-dates",
            device_id="device-dates",
            form_version=self.version,
            answers={
                "place": "Harare",
                "event_date": "2026-10-22",
                "legacy_date": "2026-11-05",
                "survey_month": "2026-10",
                "survey_year": "2026",
                "visit_day": "2026-03-04",
                "visits": [{"visited": "2026-08"}],
                "geom_point": {"type": "Point", "coordinates": [31.0, -17.0]},
            },
            user=self.user,
        )

    def _stored_dates(self):
        table = sql.Identifier(self.form.submission_table_name)
        query = sql.SQL(
            "SELECT event_date, legacy_date, survey_month, survey_year, "
            "visit_day, visits FROM {} WHERE client_submission_id = %s"
        ).format(table)
        with connection.cursor() as cursor:
            cursor.execute(query, ["sub-dates"])
            return cursor.fetchone()

    def _repeat_items(self, value):
        if isinstance(value, str):
            return json.loads(value)
        return value

    def _sync_answers(self, client_submission_id, answers, form_version=None):
        return sync_submission_to_physical_table_service(
            client_submission_id=client_submission_id,
            device_id="device-dates",
            form_version=form_version or self.version,
            answers=answers,
            user=self.user,
        )

    def _stored_column(self, client_submission_id, column, table_name=None):
        query = sql.SQL(
            "SELECT {col} FROM {table} WHERE client_submission_id = %s"
        ).format(
            col=sql.Identifier(column),
            table=sql.Identifier(table_name or self.form.submission_table_name),
        )
        with connection.cursor() as cursor:
            cursor.execute(query, [client_submission_id])
            row = cursor.fetchone()
        return None if row is None else row[0]

    def test_sync_stores_and_reads_back_date_formats(self):
        stored = self._stored_dates()
        self.assertEqual(
            stored[:5],
            (
                date(2026, 10, 22),
                date(2026, 11, 5),
                date(2026, 10, 1),
                date(2026, 1, 1),
                date(2026, 3, 4),
            ),
        )
        visits = self._repeat_items(stored[5])
        self.assertEqual(visits, [{"visited": "2026-08"}])

        listed = self.client.get(
            reverse("web_data:data_paginated", kwargs={"form_id": self.form.id})
        )
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        row = listed.json()["data"][0]
        self.assertEqual(row["event_date"], "2026-10-22")
        self.assertEqual(row["legacy_date"], "2026-11-05")
        self.assertEqual(row["survey_month"], "2026-10")
        self.assertEqual(row["survey_year"], "2026")
        self.assertEqual(row["visit_day"], "2026-03-04")
        self.assertEqual(self._repeat_items(row["visits"]), [{"visited": "2026-08"}])

        detail = self.client.get(
            reverse(
                "web_data:data_detail",
                kwargs={"form_id": self.form.id, "row_id": row["id"]},
            )
        )
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        answers = detail.json()["answers"]
        self.assertEqual(answers["survey_month"], "2026-10")
        self.assertEqual(answers["survey_year"], "2026")
        self.assertEqual(answers["legacy_date"], "2026-11-05")
        self.assertEqual(answers["visit_day"], "2026-03-04")

        geojson = self.client.get(
            reverse("web_data:geojson", kwargs={"form_id": self.form.id})
        )
        self.assertEqual(geojson.status_code, status.HTTP_200_OK)
        props = geojson.json()["features"][0]["properties"]
        self.assertEqual(props["survey_month"], "2026-10")
        self.assertEqual(props["survey_year"], "2026")
        self.assertEqual(props["event_date"], "2026-10-22")

    def test_bad_date_value_fails_the_submission(self):
        from apps.sync.services.sync_services import bulk_sync_submissions_service

        before = self._stored_dates()
        with self.assertRaises(DataError):
            sync_submission_to_physical_table_service(
                client_submission_id="sub-bad-month-13",
                device_id="device-dates",
                form_version=self.version,
                answers={"place": "Should not stick", "survey_month": "2026-13"},
                user=self.user,
            )
        with self.assertRaises(DataError):
            sync_submission_to_physical_table_service(
                client_submission_id="sub-bad-collection",
                device_id="device-dates",
                form_version=self.version,
                answers={"place": "Should not stick", "visits": [{"visited": "2026-13"}]},
                user=self.user,
            )
        self.assertEqual(self._stored_dates(), before)

        result = bulk_sync_submissions_service(
            device_id="device-dates",
            submissions_list=[
                {
                    "client_submission_id": "sub-bulk-bad",
                    "form_version_id": str(self.version.id),
                    "answers": {
                        "place": "Should not stick",
                        "survey_month": "2026",
                    },
                },
                {
                    "client_submission_id": "sub-bulk-good",
                    "form_version_id": str(self.version.id),
                    "answers": {"place": "Good row", "survey_month": "2026-09"},
                },
            ],
            user=self.user,
        )
        self.assertEqual(result["total_failed"], 1)
        self.assertEqual(result["total_success"], 1)
        self.assertEqual(result["submissions"][0]["status"], "failed")
        self.assertIn("survey_month", result["submissions"][0]["error"])

        listed = self.client.get(
            reverse("web_data:data_paginated", kwargs={"form_id": self.form.id})
        )
        places = {row.get("place") for row in listed.json()["data"]}
        self.assertIn("Good row", places)
        self.assertNotIn("Should not stick", places)
        good = next(row for row in listed.json()["data"] if row.get("place") == "Good row")
        self.assertEqual(good["survey_month"], "2026-09")

    def test_csv_export_shows_month_year(self):
        url = reverse("web_data:data_export", kwargs={"form_id": self.form.id})
        response = self.client.get(url, {"export_format": "csv"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rows = list(csv.DictReader(StringIO(response.content.decode("utf-8-sig"))))
        self.assertEqual(rows[0]["Survey month"], "2026-10")
        self.assertEqual(rows[0]["Survey year"], "2026")
        self.assertEqual(rows[0]["Event date"], "2026-10-22")
        self.assertEqual(rows[0]["Legacy date"], "2026-11-05")
        self.assertEqual(rows[0]["Visit day"], "2026-03-04")

        json_response = self.client.get(url, {"export_format": "json"})
        record = json.loads(json_response.content.decode("utf-8"))["data"][0]
        self.assertEqual(record["survey_month"], "2026-10")

        kml = self.client.get(url, {"export_format": "kml"})
        self.assertIn(
            '<Data name="survey_month"><value>2026-10</value></Data>',
            kml.content.decode("utf-8"),
        )

        xlsx = self.client.get(url, {"export_format": "xlsx"})
        with zipfile.ZipFile(BytesIO(xlsx.content)) as workbook:
            sheet = workbook.read("xl/worksheets/sheet1.xml").decode("utf-8")
        self.assertIn(">2026-10<", sheet)
        self.assertNotIn(">2026-10-01<", sheet)
        self.assertNotIn(">2026-01-01<", sheet)

    def test_full_date_without_format_is_stored_as_that_day(self):
        cases = (
            ("legacy_date", "2026-10-22T10:00:00.000", "sub-legacy-stamp"),
            ("legacy_date", "2026/10/22", "sub-legacy-slash"),
            ("event_date", "2026-10-22T10:00:00.000", "sub-full-stamp"),
            ("event_date", "2026/10/22", "sub-full-slash"),
        )
        for column, value, submission_id in cases:
            self._sync_answers(submission_id, {column: value})
            self.assertEqual(
                self._stored_column(submission_id, column),
                date(2026, 10, 22),
            )

    def test_incomplete_full_date_is_refused_by_postgres(self):
        cases = (
            ("event_date", "2026-10", "sub-full-month"),
            ("event_date", "2026", "sub-full-year"),
            ("legacy_date", "2026-10", "sub-legacy-month"),
            ("legacy_date", "2026", "sub-legacy-year"),
        )
        for column, value, submission_id in cases:
            with self.assertRaises(DataError) as caught:
                self._sync_answers(submission_id, {column: value})
            self.assertNotIn(f"({column})", str(caught.exception))
            self.assertIsNone(self._stored_column(submission_id, column))

    def test_collection_date_without_format_is_stored_as_sent(self):
        sent = [{"loose_when": "22/10/2026"}]
        self._sync_answers("sub-loose-collection", {"loose_visits": sent})
        stored = self._stored_column("sub-loose-collection", "loose_visits")
        self.assertEqual(self._repeat_items(stored), sent)

    def test_collection_date_format_checks_and_keeps_the_sent_value(self):
        sent_month = [{"visited": "2026-10-22T10:00:00.000"}]
        self._sync_answers("sub-collection-month", {"visits": sent_month})
        stored_month = self._stored_column("sub-collection-month", "visits")
        self.assertEqual(self._repeat_items(stored_month), sent_month)

        sent_day = [{"visited_on": "2026-10-22 10:00:00"}]
        self._sync_answers("sub-collection-day", {"visits": sent_day})
        stored_day = self._stored_column("sub-collection-day", "visits")
        self.assertEqual(self._repeat_items(stored_day), sent_day)

        with self.assertRaises(DataError):
            self._sync_answers(
                "sub-collection-bad-day",
                {"visits": [{"visited_on": "2026-02-30"}]},
            )
        self.assertIsNone(self._stored_column("sub-collection-bad-day", "visits"))

    def test_shorter_formats_accept_a_longer_date(self):
        cases = (
            ("survey_month", "2026-10", date(2026, 10, 1), "sub-month-short"),
            ("survey_month", "2026-10-22", date(2026, 10, 1), "sub-month-day"),
            (
                "survey_month",
                "2026-10-22T10:00:00.000",
                date(2026, 10, 1),
                "sub-month-t",
            ),
            (
                "survey_month",
                "2026-10-22 10:00:00",
                date(2026, 10, 1),
                "sub-month-space",
            ),
            ("survey_year", "2026", date(2026, 1, 1), "sub-year-short"),
            ("survey_year", "2026-10", date(2026, 1, 1), "sub-year-month"),
            ("survey_year", "2026-10-22", date(2026, 1, 1), "sub-year-day"),
            (
                "survey_year",
                "2026-10-22T10:00:00.000",
                date(2026, 1, 1),
                "sub-year-t",
            ),
            (
                "survey_year",
                "2026-10-22 10:00:00",
                date(2026, 1, 1),
                "sub-year-space",
            ),
        )
        for column, value, stored, submission_id in cases:
            self._sync_answers(submission_id, {column: value})
            self.assertEqual(self._stored_column(submission_id, column), stored)

    def test_shorter_formats_refuse_impossible_values(self):
        refused = (
            ("survey_month", "2026-13-01", "sub-bad-month-day"),
            ("survey_month", "2026-02-30", "sub-bad-feb-30"),
            ("survey_month", "2026", "sub-bad-year-on-month"),
            ("survey_year", 2026, "sub-bad-year-number"),
        )
        for column, value, submission_id in refused:
            with self.assertRaises(DataError):
                self._sync_answers(
                    submission_id,
                    {"place": "Should not stick", column: value},
                )
            self.assertIsNone(self._stored_column(submission_id, column))

    def test_reads_use_published_format_when_draft_changes_it(self):
        schema = copy.deepcopy(self.version.schema)
        for question in schema["questions"]:
            if question.get("id") in ("event_date", "survey_month"):
                question["dateFormat"] = "year"
        draft = FormVersion.objects.create(
            form=self.form,
            version_number=2,
            version_label="2.0",
            schema=schema,
            checksum=calculate_form_checksum_service(schema),
            column_mapping=dict(self.version.column_mapping),
            created_by=self.user,
            is_published=False,
        )
        self.form.current_version = draft
        self.form.save()

        listed = self.client.get(
            reverse("web_data:data_paginated", kwargs={"form_id": self.form.id})
        )
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        row = listed.json()["data"][0]
        self.assertEqual(row["event_date"], "2026-10-22")
        self.assertEqual(row["survey_month"], "2026-10")

        detail = self.client.get(
            reverse(
                "web_data:data_detail",
                kwargs={"form_id": self.form.id, "row_id": row["id"]},
            )
        )
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        answers = detail.json()["answers"]
        self.assertEqual(answers["event_date"], "2026-10-22")
        self.assertEqual(answers["survey_month"], "2026-10")

        exported = self.client.get(
            reverse("web_data:data_export", kwargs={"form_id": self.form.id}),
            {"export_format": "csv"},
        )
        csv_rows = list(
            csv.DictReader(StringIO(exported.content.decode("utf-8-sig")))
        )
        self.assertEqual(csv_rows[0]["Event date"], "2026-10-22")
        self.assertEqual(csv_rows[0]["Survey month"], "2026-10")

        geojson = self.client.get(
            reverse("web_data:geojson", kwargs={"form_id": self.form.id})
        )
        props = geojson.json()["features"][0]["properties"]
        self.assertEqual(props["event_date"], "2026-10-22")
        self.assertEqual(props["survey_month"], "2026-10")

    def test_reads_use_the_draft_format_when_nothing_is_published(self):
        form = Form.objects.create(
            project=self.project,
            title="Draft Date Form",
            slug="date-form-draft-only",
            status="draft",
            geometry_type="point",
            created_by=self.user,
        )
        schema = {
            "formId": str(form.id),
            "title": "Draft Date Form",
            "version": "1.0",
            "mode": "form_first",
            "geometryType": "point",
            "projectId": "DATE-1",
            "questions": [
                {"id": "place", "type": "text", "label": "Place"},
                {
                    "id": "survey_year",
                    "type": "date",
                    "label": "Survey year",
                    "dateFormat": "year",
                },
                {"id": "geom_point", "type": "point", "label": "Location"},
            ],
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
            is_published=False,
        )
        version.physical_table_name = generate_form_table_name_service(
            form.slug, 1, form.id
        )
        version.save()
        create_physical_form_table_service(version)
        form.current_version = version
        form.submission_table_name = version.physical_table_name
        form.save()

        self._sync_answers(
            "sub-draft-only",
            {
                "place": "Draft row",
                "survey_year": "2026",
                "geom_point": {"type": "Point", "coordinates": [31.0, -17.0]},
            },
            form_version=version,
        )
        self.assertEqual(
            self._stored_column(
                "sub-draft-only", "survey_year", version.physical_table_name
            ),
            date(2026, 1, 1),
        )

        listed = self.client.get(
            reverse("web_data:data_paginated", kwargs={"form_id": form.id})
        )
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        row = listed.json()["data"][0]
        self.assertEqual(row["survey_year"], "2026")

        detail = self.client.get(
            reverse(
                "web_data:data_detail",
                kwargs={"form_id": form.id, "row_id": row["id"]},
            )
        )
        self.assertEqual(detail.json()["answers"]["survey_year"], "2026")

        exported = self.client.get(
            reverse("web_data:data_export", kwargs={"form_id": form.id}),
            {"export_format": "csv"},
        )
        csv_rows = list(
            csv.DictReader(StringIO(exported.content.decode("utf-8-sig")))
        )
        self.assertEqual(csv_rows[0]["Survey year"], "2026")

        geojson = self.client.get(
            reverse("web_data:geojson", kwargs={"form_id": form.id})
        )
        self.assertEqual(
            geojson.json()["features"][0]["properties"]["survey_year"],
            "2026",
        )
