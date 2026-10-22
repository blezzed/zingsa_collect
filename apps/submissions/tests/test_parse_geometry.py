from django.test import SimpleTestCase

from apps.submissions.services.submission_services import parse_geometry
from apps.submissions.services.web_data_services import _coerce_to_geojson


LINE = {
    "type": "line",
    "latitude": -17.2,
    "longitude": 31.2,
    "points": [
        {"latitude": -17.2, "longitude": 31.2},
        {"latitude": -17.3, "longitude": 31.3},
        {"latitude": -17.4, "longitude": 31.4},
    ],
}
POLYGON = {
    "type": "polygon",
    "latitude": -17.5,
    "longitude": 31.5,
    "points": [
        {"latitude": -17.5, "longitude": 31.5},
        {"latitude": -17.6, "longitude": 31.6},
        {"latitude": -17.55, "longitude": 31.7},
    ],
}


class ParseGeometryTests(SimpleTestCase):
    def test_line_payload_is_not_reduced_to_its_first_point(self):
        wkt = parse_geometry(LINE, "GEOMETRY(LineString, 4326)")
        self.assertTrue(wkt.startswith("LINESTRING"))
        self.assertNotIn("POINT", wkt)

    def test_polygon_payload_is_not_reduced_to_its_first_point(self):
        wkt = parse_geometry(POLYGON, "GEOMETRY(Polygon, 4326)")
        self.assertTrue(wkt.startswith("POLYGON"))

    def test_mixed_column_keeps_line_and_polygon(self):
        line = parse_geometry(LINE, "GEOMETRY(Geometry, 4326)")
        polygon = parse_geometry(POLYGON, "GEOMETRY(Geometry, 4326)")
        self.assertTrue(line.startswith("LINESTRING"))
        self.assertTrue(polygon.startswith("POLYGON"))

    def test_point_payload_stays_a_point(self):
        wkt = parse_geometry(
            {"latitude": -17.82, "longitude": 31.03},
            "GEOMETRY(Point, 4326)",
        )
        self.assertEqual(wkt, "POINT(31.03 -17.82)")

    def test_read_path_keeps_explicit_line_on_a_geometry_field(self):
        geom = _coerce_to_geojson(LINE, expected_type="geometry")
        self.assertEqual(geom["type"], "LineString")
        self.assertEqual(len(geom["coordinates"]), 3)
