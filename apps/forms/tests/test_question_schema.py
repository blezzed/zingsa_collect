from django.test import TestCase

from apps.forms.services.form_services import (
    generate_column_mapping_service,
    map_question_type_to_pg,
    validate_form_schema_service,
)
from apps.forms.services.question_schema import (
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

    def test_walk_storage_skips_note(self):
        questions = [
            {"id": "intro", "type": "note", "label": "Instructions"},
            {"id": "name", "type": "text", "label": "Name"},
        ]
        stored = [q["id"] for q in walk_storage_questions(questions)]
        self.assertEqual(stored, ["name"])
