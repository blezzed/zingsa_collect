from django.test import TestCase

from apps.forms.services.form_services import (
    generate_column_mapping_service,
    map_question_type_to_pg,
    validate_form_schema_service,
)
from apps.forms.services.question_schema import (
    resolve_geometry_type,
    schema_has_spatial_questions,
    walk_storage_questions,
)


GARDEN_COLLECTION_SCHEMA = {
    "formId": "garden_form",
    "title": "Garden Registry",
    "version": "1.0",
    "mode": "form_first",
    "projectId": "PROJ-001",
    "questions": [
        {
            "id": "villageName",
            "type": "text",
            "label": "Village Name",
        },
        {
            "id": "gardenDetails",
            "type": "collection",
            "label": "Garden Details",
            "itemLabel": "Garden Detail",
            "questions": [
                {
                    "id": "fieldStatus",
                    "type": "radio",
                    "label": "Field Status",
                    "options": [{"value": "planted", "label": "Planted"}],
                },
                {
                    "id": "gardenBoundary",
                    "type": "polygon",
                    "label": "Garden Boundary",
                },
                {
                    "id": "productivityScore",
                    "type": "slider",
                    "label": "Productivity Score",
                    "min": 1,
                    "max": 10,
                },
            ],
        },
    ],
}


class QuestionSchemaServicesTests(TestCase):
    def test_validate_collection_schema(self):
        validate_form_schema_service(GARDEN_COLLECTION_SCHEMA)

    def test_collection_maps_to_jsonb_not_children(self):
        mapping, db_types = generate_column_mapping_service(
            GARDEN_COLLECTION_SCHEMA["questions"]
        )
        self.assertIn("gardenDetails", mapping)
        self.assertEqual(db_types[mapping["gardenDetails"]], "JSONB")
        self.assertNotIn("gardenBoundary", mapping)
        self.assertNotIn("fieldStatus", mapping)

    def test_nested_spatial_inside_collection_detected(self):
        self.assertTrue(
            schema_has_spatial_questions(GARDEN_COLLECTION_SCHEMA["questions"])
        )

    def test_new_field_type_pg_mappings(self):
        self.assertEqual(map_question_type_to_pg({"type": "collection"}), "JSONB")
        self.assertEqual(map_question_type_to_pg({"type": "contact"}), "JSONB")
        self.assertEqual(map_question_type_to_pg({"type": "calculated"}), "NUMERIC")
        self.assertEqual(map_question_type_to_pg({"type": "rating"}), "INTEGER")
        self.assertEqual(map_question_type_to_pg({"type": "slider", "step": 1}), "INTEGER")
        self.assertEqual(map_question_type_to_pg({"type": "password"}), "VARCHAR(255)")

    def test_group_children_get_columns(self):
        questions = [
            {
                "id": "household",
                "type": "group",
                "label": "Household",
                "questions": [
                    {"id": "head_name", "type": "text", "label": "Head of household"},
                ],
            },
        ]
        mapping, _ = generate_column_mapping_service(questions)
        self.assertIn("head_name", mapping)
        self.assertNotIn("household", mapping)

    def test_infer_geometry_type_from_questions(self):
        from apps.forms.services.question_schema import infer_geometry_type_from_questions

        self.assertEqual(
            infer_geometry_type_from_questions(
                [{"id": "a", "type": "location", "label": "A"}]
            ),
            "point",
        )
        self.assertEqual(
            infer_geometry_type_from_questions(
                [
                    {"id": "a", "type": "point", "label": "A"},
                    {"id": "b", "type": "polygon", "label": "B"},
                ]
            ),
            "mixed",
        )
        self.assertEqual(
            infer_geometry_type_from_questions(
                GARDEN_COLLECTION_SCHEMA["questions"]
            ),
            "polygon",
        )

    def test_mixed_selection_is_not_rewritten_to_point(self):
        questions = [{"id": "geom", "type": "location", "label": "Location"}]
        self.assertEqual(resolve_geometry_type("mixed", questions), "mixed")
        self.assertEqual(questions[0]["type"], "geometry")
        _, db_types = generate_column_mapping_service(questions)
        self.assertEqual(db_types["geom"], "GEOMETRY(Geometry, 4326)")

    def test_line_and_polygon_selection_keep_their_column_type(self):
        line = [{"id": "geom", "type": "location", "label": "Location"}]
        self.assertEqual(resolve_geometry_type("line", line), "line")
        self.assertEqual(line[0]["type"], "line")
        _, line_types = generate_column_mapping_service(line)
        self.assertEqual(line_types["geom"], "GEOMETRY(LineString, 4326)")

        polygon = [{"id": "geom", "type": "point", "label": "Location"}]
        self.assertEqual(resolve_geometry_type("polygon", polygon), "polygon")
        self.assertEqual(polygon[0]["type"], "polygon")
        _, polygon_types = generate_column_mapping_service(polygon)
        self.assertEqual(polygon_types["geom"], "GEOMETRY(Polygon, 4326)")

    def test_several_shapes_stay_mixed(self):
        questions = [
            {"id": "boundary", "type": "line", "label": "Line"},
            {"id": "parcel", "type": "polygon", "label": "Polygon"},
        ]
        self.assertEqual(resolve_geometry_type("line", questions), "mixed")
        self.assertEqual(questions[0]["type"], "line")
        self.assertEqual(questions[1]["type"], "polygon")

    def test_walk_storage_skips_note(self):
        questions = [
            {"id": "intro", "type": "note", "label": "Instructions"},
            {"id": "name", "type": "text", "label": "Name"},
        ]
        stored = [q["id"] for q in walk_storage_questions(questions)]
        self.assertEqual(stored, ["name"])

    def test_datetime_maps_to_timestamptz(self):
        self.assertEqual(map_question_type_to_pg({"type": "datetime"}), "TIMESTAMPTZ")

    def test_rejects_unknown_type(self):
        with self.assertRaises(Exception):
            validate_form_schema_service(
                {
                    **GARDEN_COLLECTION_SCHEMA,
                    "questions": [
                        {"id": "x", "type": "not_a_type", "label": "X"},
                    ],
                }
            )

    def test_rejects_duplicate_ids(self):
        with self.assertRaises(Exception):
            validate_form_schema_service(
                {
                    **GARDEN_COLLECTION_SCHEMA,
                    "questions": [
                        {"id": "name", "type": "text", "label": "A"},
                        {"id": "name", "type": "text", "label": "B"},
                    ],
                }
            )

    def test_choice_requires_options(self):
        with self.assertRaises(Exception):
            validate_form_schema_service(
                {
                    **GARDEN_COLLECTION_SCHEMA,
                    "questions": [
                        {"id": "status", "type": "radio", "label": "Status"},
                    ],
                }
            )

    def test_condition_operator_and_field(self):
        validate_form_schema_service(
            {
                **GARDEN_COLLECTION_SCHEMA,
                "questions": [
                    {"id": "flag", "type": "text", "label": "Flag"},
                    {
                        "id": "notes",
                        "type": "textarea",
                        "label": "Notes",
                        "condition": {
                            "field": "flag",
                            "operator": "equals",
                            "value": "yes",
                        },
                    },
                ],
            }
        )
        with self.assertRaises(Exception):
            validate_form_schema_service(
                {
                    **GARDEN_COLLECTION_SCHEMA,
                    "questions": [
                        {
                            "id": "notes",
                            "type": "textarea",
                            "label": "Notes",
                            "condition": {
                                "field": "missing",
                                "operator": "equals",
                                "value": "yes",
                            },
                        },
                    ],
                }
            )
