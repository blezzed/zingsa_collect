"""
Shared helpers for dynamic form question trees (groups, collections, GIS nesting).
Aligned with the ZINGSA Collect Question Type Specification.
"""

from rest_framework.exceptions import ValidationError

SPATIAL_QUESTION_TYPES = frozenset(
    {"location", "point", "line", "polygon", "geometry"}
)
LAYOUT_CONTAINER_TYPES = frozenset({"section", "group", "note"})
STORAGE_CONTAINER_TYPES = frozenset({"collection"})

CANONICAL_QUESTION_TYPES = frozenset(
    {
        "text",
        "textarea",
        "number",
        "date",
        "time",
        "datetime",
        "phone",
        "email",
        "url",
        "radio",
        "checkbox",
        "dropdown",
        "slider",
        "rating",
        "image",
        "video",
        "voice",
        "file",
        "signature",
        "location",
        "point",
        "line",
        "polygon",
        "collection",
        "calculated",
    }
)

# Legacy aliases still accepted on stored schemas.
SUPPORTED_QUESTION_TYPES = CANONICAL_QUESTION_TYPES | frozenset(
    {
        "select",
        "audio",
        "password",
        "contact",
        "barcode",
        "qr",
        "section",
        "group",
        "note",
        "geometry",
    }
)

CHOICE_TYPES = frozenset({"radio", "checkbox", "dropdown", "select"})

CONDITION_OPERATORS = frozenset(
    {
        "equals",
        "not_equals",
        "contains",
        "not_contains",
        "greater_than",
        "less_than",
        "greater_than_or_equal",
        "less_than_or_equal",
        "is_empty",
        "is_not_empty",
        "starts_with",
        "ends_with",
        "matches",
    }
)

OPERATORS_WITHOUT_VALUE = frozenset({"is_empty", "is_not_empty"})


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


def _require_bool(q: dict, key: str, path: str) -> None:
    if key in q and q[key] is not None and not isinstance(q[key], bool):
        raise ValidationError(f"{path} '{key}' must be a boolean.")


def _optional_number(q: dict, key: str, path: str) -> None:
    if key not in q or q[key] is None:
        return
    if not isinstance(q[key], (int, float)) or isinstance(q[key], bool):
        raise ValidationError(f"{path} '{key}' must be a number.")


def _optional_positive(q: dict, key: str, path: str) -> None:
    _optional_number(q, key, path)
    if key in q and q[key] is not None and q[key] <= 0:
        raise ValidationError(f"{path} '{key}' must be greater than 0.")


def _validate_options(q: dict, path: str) -> None:
    options = q.get("options")
    if not isinstance(options, list) or not options:
        raise ValidationError(f"{path} must include a non-empty 'options' array.")
    for oi, opt in enumerate(options):
        if not isinstance(opt, dict):
            raise ValidationError(f"{path} options[{oi}] must be an object.")
        if not str(opt.get("value") or "").strip():
            raise ValidationError(f"{path} options[{oi}] is missing 'value'.")
        if not str(opt.get("label") or "").strip():
            raise ValidationError(f"{path} options[{oi}] is missing 'label'.")


def _validate_condition(q: dict, path: str, known_ids: set[str] | None) -> None:
    condition = q.get("condition")
    if condition is None:
        return
    if not isinstance(condition, dict):
        raise ValidationError(f"{path} 'condition' must be an object.")
    field = condition.get("field")
    operator = condition.get("operator")
    if not str(field or "").strip():
        raise ValidationError(f"{path} condition.field is required.")
    if operator not in CONDITION_OPERATORS:
        raise ValidationError(f"{path} condition.operator is not supported.")
    if operator not in OPERATORS_WITHOUT_VALUE and "value" not in condition:
        raise ValidationError(f"{path} condition.value is required for '{operator}'.")
    if known_ids is not None and field not in known_ids:
        raise ValidationError(
            f"{path} condition.field '{field}' does not match a question ID."
        )


def _validate_type_specific(q: dict, q_type: str, path: str) -> None:
    _require_bool(q, "required", path)
    _require_bool(q, "smartenable", path)
    _require_bool(q, "scanEnabled", path)
    _require_bool(q, "autocapture", path)
    _require_bool(q, "multiselect", path)
    _require_bool(q, "noUpload", path)

    if q_type in ("text", "textarea"):
        _optional_number(q, "minLength", path)
        _optional_number(q, "maxLength", path)
        min_len = q.get("minLength")
        max_len = q.get("maxLength")
        if (
            isinstance(min_len, (int, float))
            and isinstance(max_len, (int, float))
            and min_len > max_len
        ):
            raise ValidationError(f"{path} minLength cannot exceed maxLength.")

    if q_type == "number":
        _optional_number(q, "min", path)
        _optional_number(q, "max", path)
        _optional_number(q, "decimalPlaces", path)
        numeric_type = q.get("numericType")
        if numeric_type is not None and numeric_type not in (
            "integer",
            "decimal",
            "float",
        ):
            raise ValidationError(
                f"{path} numericType must be integer, decimal, or float."
            )
        if (
            isinstance(q.get("min"), (int, float))
            and isinstance(q.get("max"), (int, float))
            and q["min"] > q["max"]
        ):
            raise ValidationError(f"{path} min cannot exceed max.")

    if q_type == "slider":
        for key in ("min", "max"):
            if key not in q:
                raise ValidationError(f"{path} '{key}' is required for slider.")
            _optional_number(q, key, path)
        _optional_number(q, "step", path)
        if q["min"] > q["max"]:
            raise ValidationError(f"{path} min cannot exceed max.")

    if q_type == "rating" and "maxStars" in q:
        _optional_positive(q, "maxStars", path)

    if q_type in CHOICE_TYPES:
        _validate_options(q, path)
        _optional_number(q, "minSelections", path)
        _optional_number(q, "maxSelections", path)
        min_sel = q.get("minSelections")
        max_sel = q.get("maxSelections")
        if (
            isinstance(min_sel, (int, float))
            and isinstance(max_sel, (int, float))
            and min_sel > max_sel
        ):
            raise ValidationError(f"{path} minSelections cannot exceed maxSelections.")

    if q_type == "image":
        _optional_positive(q, "maxPhotos", path)
    if q_type in ("video", "voice"):
        _optional_positive(q, "maxDuration", path)
    if q_type == "file":
        _optional_positive(q, "maxFiles", path)
        allowed = q.get("allowedTypes")
        if allowed is not None and (
            not isinstance(allowed, list)
            or not all(isinstance(item, str) for item in allowed)
        ):
            raise ValidationError(f"{path} allowedTypes must be an array of strings.")
    if q_type == "location":
        _optional_positive(q, "maxAccuracy", path)
    if q_type == "calculated" and "expression" in q and not str(q.get("expression") or "").strip():
        raise ValidationError(f"{path} calculated questions require 'expression'.")


def validate_questions_recursive(
    questions: list,
    path: str = "questions",
    known_ids: set[str] | None = None,
) -> None:
    if not isinstance(questions, list):
        raise ValidationError(f"Schema '{path}' must be a JSON array.")

    if path == "questions" and len(questions) == 0:
        raise ValidationError("Schema 'questions' array cannot be empty.")

    if known_ids is None:
        known_ids = set()
        for q in walk_all_questions(questions):
            qid = q.get("id")
            if isinstance(qid, str) and qid.strip():
                if qid in known_ids:
                    raise ValidationError(f"Duplicate question id '{qid}'.")
                known_ids.add(qid)

    for idx, q in enumerate(questions):
        q_path = f"{path}[{idx}]"
        if not isinstance(q, dict):
            raise ValidationError(f"Question at {q_path} must be a JSON object.")

        for qk in ("id", "type", "label"):
            if qk not in q:
                raise ValidationError(
                    f"Question at {q_path} is missing required field '{qk}'."
                )
            val = q[qk]
            if isinstance(val, str) and not val.strip():
                raise ValidationError(
                    f"Question at {q_path} field '{qk}' cannot be empty."
                )

        q_type = (q.get("type") or "").lower()
        if q_type not in SUPPORTED_QUESTION_TYPES:
            raise ValidationError(f"Question at {q_path} has unsupported type '{q_type}'.")

        _validate_type_specific(q, q_type, q_path)
        _validate_condition(q, q_path, known_ids)

        nested = nested_questions(q)
        if q_type == "collection" and not nested:
            raise ValidationError(
                f"Collection at {q_path} must include a non-empty 'questions' array."
            )
        if nested:
            validate_questions_recursive(nested, f"{q_path}.questions", known_ids)


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
