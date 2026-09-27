from django.test import SimpleTestCase

from apps.submissions.services.web_data_services import build_kml_bytes


class BuildKmlBytesTests(SimpleTestCase):
    def test_point_line_and_polygon(self):
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [31.05, -17.82]},
                    "properties": {"id": 1, "field_label": "Location Point"},
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[31.0, -17.8], [31.1, -17.9]],
                    },
                    "properties": {"id": 2, "field_label": "Track"},
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [31.0, -17.8],
                                [31.1, -17.8],
                                [31.1, -17.9],
                                [31.0, -17.9],
                            ]
                        ],
                    },
                    "properties": {"id": 3, "field_label": "Area"},
                },
            ],
        }
        kml = build_kml_bytes(geojson, document_name="Geo Form").decode("utf-8")
        self.assertIn("<kml xmlns=\"http://www.opengis.net/kml/2.2\">", kml)
        self.assertIn("<name>Geo Form</name>", kml)
        self.assertEqual(kml.count("<Placemark>"), 3)
        self.assertIn("31.05,-17.82,0", kml)
        self.assertIn("<LineString>", kml)
        self.assertIn("<Polygon>", kml)
        self.assertIn("<name>Location Point (1)</name>", kml)
        self.assertIn('name="field_label"', kml)

    def test_skips_features_without_geometry(self):
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "geometry": None, "properties": {"id": 1}},
            ],
        }
        kml = build_kml_bytes(geojson).decode("utf-8")
        self.assertNotIn("<Placemark>", kml)
