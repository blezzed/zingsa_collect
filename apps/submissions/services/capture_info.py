"""Store and display optional GPS and device details sent with a submission.

A bad, missing, or oversized ``capture_info`` is dropped. It must not reject
the submission: the answers are the record, and this block is only a quality note.
"""

import logging
import math
from datetime import datetime
from itertools import islice

from django.db import transaction

from apps.forms.services.question_schema import walk_all_questions
from apps.submissions.models import SubmissionIndex

logger = logging.getLogger(__name__)

CAPTURE_COLUMN_IDS = ("gps_accuracy_m", "device_model", "app_version")
DEVICE_KEYS = (
    "platform",
    "os_version",
    "manufacturer",
    "model",
    "app_version",
)
MAX_TEXT_LENGTH = 100
MAX_GPS_ENTRIES = 50
MAX_ACCURACY_M = 100000
CAPTURE_COLUMN_LABELS = {
    "gps_accuracy_m": "GPS Accuracy (m)",
    "device_model": "Device Model",
    "app_version": "App Version",
}

EMPTY_CAPTURE_COLUMNS = {
    "gps_accuracy_m": "",
    "device_model": "",
    "app_version": "",
}


def empty_capture_columns() -> dict:
    return dict(EMPTY_CAPTURE_COLUMNS)


def prepare_capture_info(raw) -> tuple[dict, float | None]:
    """Return ``(stored_capture_info, gps_accuracy_m)``. Never raises."""
    try:
        return sanitize_capture_info(raw)
    except Exception:
        logger.exception(
            "Dropping capture_info after an unexpected error; the submission will still be saved"
        )
        return {}, None


def sanitize_capture_info(raw) -> tuple[dict, float | None]:
    """Keep only the allowed keys and values. Drop anything that fails a check."""
    if not isinstance(raw, dict):
        return {}, None

    gps = _sanitize_gps(raw.get("gps"))
    device = _sanitize_device(raw.get("device"))
    stored: dict = {}
    if gps:
        stored["gps"] = gps
    if device:
        stored["device"] = device
    return stored, _largest_accuracy(gps)


def create_submission_index(**kwargs) -> SubmissionIndex:
    """
    Create the index row.

    If saving ``capture_info`` fails, save the same row without it. The answers
    are already in the physical table inside this transaction, and a quality
    note must not roll them back.
    """
    try:
        with transaction.atomic():
            return SubmissionIndex.objects.create(**kwargs)
    except Exception:
        capture_info = kwargs.get("capture_info") or {}
        accuracy = kwargs.get("gps_accuracy_m")
        if not capture_info and accuracy is None:
            raise
        logger.exception(
            "Saving the submission without capture_info after an unexpected error"
        )
        retry = dict(kwargs)
        retry["capture_info"] = {}
        retry["gps_accuracy_m"] = None
        return SubmissionIndex.objects.create(**retry)


def capture_column_ids_owned_by_questions(form) -> set[str]:
    """Question ids that already use a capture column name. Those answers win."""
    version = getattr(form, "current_version", None)
    schema = getattr(version, "schema", None) or {}
    questions = schema.get("questions") or []
    if not isinstance(questions, list):
        return set()
    owned = set()
    for question in walk_all_questions(questions):
        question_id = question.get("id")
        if question_id in CAPTURE_COLUMN_IDS:
            owned.add(question_id)
    return owned


def capture_export_headers(form) -> list[dict]:
    owned = capture_column_ids_owned_by_questions(form)
    headers = []
    for column_id in CAPTURE_COLUMN_IDS:
        if column_id in owned:
            continue
        headers.append({
            "id": column_id,
            "label": CAPTURE_COLUMN_LABELS[column_id],
            "type": "number" if column_id == "gps_accuracy_m" else "text",
        })
    return headers


def capture_display_by_row_id(form, row_ids) -> dict[int, dict]:
    """One query for the whole page. Missing rows are left out of the map."""
    ids = []
    for row_id in row_ids:
        parsed = _row_id(row_id)
        if parsed is not None:
            ids.append(parsed)
    if not ids:
        return {}

    queryset = SubmissionIndex.objects.filter(form=form, physical_row_id__in=ids)
    table_name = getattr(form, "submission_table_name", None) or ""
    if table_name:
        queryset = queryset.filter(physical_table_name=table_name)

    found: dict[int, dict] = {}
    columns = queryset.order_by("-created_at").values_list(
        "physical_row_id", "capture_info", "gps_accuracy_m"
    )
    for physical_row_id, capture_info, gps_accuracy_m in columns:
        row_key = _row_id(physical_row_id)
        if row_key is None or row_key in found:
            continue
        found[row_key] = _display_fields(capture_info, gps_accuracy_m)
    return found


def apply_capture_columns(form, rows: list[dict]) -> None:
    """Add the three capture columns in place. Does not query once per row."""
    if not rows:
        return
    owned = capture_column_ids_owned_by_questions(form)
    by_row = capture_display_by_row_id(form, [row.get("id") for row in rows])
    for row in rows:
        row_key = _row_id(row.get("id"))
        display = by_row.get(row_key) if row_key is not None else None
        if display is None:
            display = empty_capture_columns()
        for key, value in display.items():
            if key in owned:
                continue
            row[key] = value


def _display_fields(capture_info, gps_accuracy_m) -> dict:
    if not isinstance(capture_info, dict) or not capture_info:
        return empty_capture_columns()
    device = capture_info.get("device")
    if not isinstance(device, dict):
        device = {}
    manufacturer = device.get("manufacturer")
    model = device.get("model")
    parts = []
    if isinstance(manufacturer, str) and manufacturer.strip():
        parts.append(manufacturer.strip())
    if isinstance(model, str) and model.strip():
        parts.append(model.strip())
    app_version = device.get("app_version")
    if not isinstance(app_version, str):
        app_version = ""
    return {
        "gps_accuracy_m": "" if gps_accuracy_m is None else gps_accuracy_m,
        "device_model": " ".join(parts),
        "app_version": app_version,
    }


def _sanitize_gps(raw) -> dict:
    if not isinstance(raw, dict):
        return {}
    cleaned = {}
    for key, value in islice(raw.items(), MAX_GPS_ENTRIES):
        question_id = _question_id(key)
        if question_id is None:
            continue
        reading = _sanitize_reading(value)
        if reading:
            cleaned[question_id] = reading
    return cleaned


def _sanitize_reading(raw) -> dict | None:
    if not isinstance(raw, dict):
        return None
    reading = {}
    if "accuracy_m" in raw:
        accuracy = _accuracy_m(raw.get("accuracy_m"))
        if accuracy is not None:
            reading["accuracy_m"] = accuracy
    if "altitude_m" in raw:
        altitude = _finite_number(raw.get("altitude_m"))
        if altitude is not None:
            reading["altitude_m"] = altitude
    if "provider" in raw:
        provider = _limited_string(raw.get("provider"))
        if provider is not None:
            reading["provider"] = provider
    if "captured_at" in raw:
        captured_at = _iso8601(raw.get("captured_at"))
        if captured_at is not None:
            reading["captured_at"] = captured_at
    if "mock_location" in raw and isinstance(raw.get("mock_location"), bool):
        reading["mock_location"] = raw.get("mock_location")
    return reading or None


def _sanitize_device(raw) -> dict:
    if not isinstance(raw, dict):
        return {}
    device = {}
    for key in DEVICE_KEYS:
        if key not in raw:
            continue
        text = _limited_string(raw.get(key))
        if text is not None:
            device[key] = text
    return device


def _largest_accuracy(gps: dict) -> float | None:
    best = None
    for reading in gps.values():
        if not isinstance(reading, dict):
            continue
        number = _finite_number(reading.get("accuracy_m"))
        if number is None or number < 0 or number > MAX_ACCURACY_M:
            continue
        as_float = float(number)
        if best is None or as_float > best:
            best = as_float
    if best is None or not math.isfinite(best):
        return None
    return best


def _accuracy_m(value):
    number = _finite_number(value)
    if number is None or number < 0 or number > MAX_ACCURACY_M:
        return None
    return number


def _finite_number(value):
    # ``bool`` is an ``int`` subclass. ``true`` is not a number here.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value):
        return None
    return value


def _limited_string(value) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if len(text) > MAX_TEXT_LENGTH:
        return None
    return text


def _iso8601(value) -> str | None:
    text = _limited_string(value)
    if not text:
        return None
    candidate = text[:-1] + "+00:00" if text.endswith(("Z", "z")) else text
    try:
        datetime.fromisoformat(candidate)
    except ValueError:
        return None
    return text


def _question_id(key) -> str | None:
    if not isinstance(key, str) or len(key) > MAX_TEXT_LENGTH:
        return None
    return key


def _row_id(value) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
