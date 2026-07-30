"""
Shared helpers for dynamic form question trees (groups, collections, GIS nesting).
Aligned with ZINGSA Collect mobile question types documentation.
"""

from rest_framework.exceptions import ValidationError

SPATIAL_QUESTION_TYPES = frozenset(
    {"location", "point", "line", "polygon", "geometry"}
)
LAYOUT_CONTAINER_TYPES = frozenset({"section", "group", "note"})
STORAGE_CONTAINER_TYPES = frozenset({"collection"})


def nested_questions(question: dict) -> list:
    nested = question.get("questions") or question.get("children")
    return nested if isinstance(nested, list) else []


def walk_all_questions(questions: list):
    """Every question node in the tree (containers and leaves)."""
    for q in questions:
        if not isinstance(q, dict):
            continue
        yield q
        for child in walk_all_questions(nested_questions(q)):
            yield child


def walk_storage_questions(questions: list):
    """
    Questions that receive a dedicated column on the physical submission table.
    - collection → one JSONB column (repeating subform payload)
    - section/group/note → layout only; children are stored as separate columns
    """
    for q in questions:
        if not isinstance(q, dict):
            continue
        q_type = (q.get("type") or "").lower()
        nested = nested_questions(q)

        if q_type in STORAGE_CONTAINER_TYPES:
            yield q
        elif q_type in LAYOUT_CONTAINER_TYPES and nested:
            for child in walk_storage_questions(nested):
                yield child
        elif nested:
            for child in walk_storage_questions(nested):
                yield child
        elif q_type in LAYOUT_CONTAINER_TYPES:
            continue
        else:
            yield q


def schema_has_spatial_questions(questions: list) -> bool:
    for q in walk_all_questions(questions):
        if q.get("type") in SPATIAL_QUESTION_TYPES:
            return True
    return False


def infer_geometry_type_from_questions(questions: list) -> str:
    """
    Derive Form.geometry_type from spatial question types in the schema.
    location/point → point; line → line; polygon → polygon; mixed types → mixed.
    """
    found = set()
    for q in walk_all_questions(questions):
        q_type = (q.get("type") or "").lower()
        if q_type not in SPATIAL_QUESTION_TYPES:
            continue
        if q_type in ("location", "point"):
            found.add("point")
        elif q_type == "line":
            found.add("line")
        elif q_type == "polygon":
            found.add("polygon")
        elif q_type == "geometry":
            found.add("mixed")
    if not found:
        return "none"
    if len(found) == 1:
        return next(iter(found))
    return "mixed"


def validate_questions_recursive(questions: list, path: str = "questions") -> None:
    if not isinstance(questions, list):
        raise ValidationError(f"Schema '{path}' must be a JSON array.")

    if path == "questions" and len(questions) == 0:
        raise ValidationError("Schema 'questions' array cannot be empty.")

    for idx, q in enumerate(questions):
        if not isinstance(q, dict):
            raise ValidationError(f"Question at {path}[{idx}] must be a JSON object.")

        for qk in ("id", "type", "label"):
            if qk not in q:
                raise ValidationError(
                    f"Question at {path}[{idx}] is missing required field '{qk}'."
                )
            val = q[qk]
            if isinstance(val, str) and not val.strip():
                raise ValidationError(
                    f"Question at {path}[{idx}] field '{qk}' cannot be empty."
                )

        q_type = (q.get("type") or "").lower()
        nested = nested_questions(q)

        if q_type == "collection" and not nested:
            raise ValidationError(
                f"Collection at {path}[{idx}] must include a non-empty 'questions' array."
            )

        if nested:
            validate_questions_recursive(nested, f"{path}[{idx}].questions")


def collection_question_columns(version) -> list[tuple[dict, str]]:
    """
    Returns (question_dict, column_name) for every collection that has a
    physical JSONB column — including collections nested under groups/sections.
    """
    if not version or not version.column_mapping:
        return []
    out = []
    seen = set()
    for q in walk_storage_questions(version.schema.get("questions", [])):
        if (q.get("type") or "").lower() != "collection":
            continue
        q_id = q.get("id")
        if not q_id or q_id not in version.column_mapping:
            continue
        col = version.column_mapping[q_id]
        if col in seen:
            continue
        seen.add(col)
        out.append((q, col))
    return out