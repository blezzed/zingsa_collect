import uuid
import json
from datetime import date, datetime

from django.db import transaction, connection, DataError
from django.utils import timezone
from django.contrib.gis.geos import GEOSGeometry
from rest_framework.exceptions import ValidationError
from psycopg2 import sql

from apps.submissions.models import SubmissionIndex, SubmissionMedia
from apps.forms.services.form_services import (
    generate_column_mapping_service,
    get_live_submission_version,
    list_physical_table_columns,
    physical_table_exists,
)
from apps.forms.services.question_schema import (
    effective_date_format,
    nested_questions,
    walk_storage_questions,
)

def _column_geometry_kind(col_type: str) -> str:
    """point / line / polygon, or any for a generic geometry column."""
    upper = (col_type or "").upper()
    if "LINESTRING" in upper:
        return "line"
    if "POLYGON" in upper:
        return "polygon"
    if "POINT" in upper and "MULTIPOINT" not in upper:
        return "point"
    return "any"


def _payload_geometry_kind(value) -> str | None:
    if not isinstance(value, dict):
        return None
    raw = (
        value.get("type")
        or value.get("geometryType")
        or value.get("shape")
        or value.get("geomType")
        or ""
    )
    return {
        "point": "point",
        "location": "point",
        "multipoint": "point",
        "line": "line",
        "linestring": "line",
        "multilinestring": "line",
        "polygon": "polygon",
        "multipolygon": "polygon",
    }.get(str(raw).strip().lower())


def _coord_pairs(points) -> list:
    coords = []
    if not isinstance(points, list):
        return coords
    for item in points:
        if isinstance(item, dict):
            lat = item.get("latitude", item.get("lat"))
            lng = item.get("longitude", item.get("lng", item.get("lon")))
            if lat is None or lng is None:
                continue
            try:
                coords.append((float(lng), float(lat)))
            except (TypeError, ValueError):
                continue
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            try:
                coords.append((float(item[0]), float(item[1])))
            except (TypeError, ValueError):
                continue
    return coords


def _wkt_for_kind(coords, kind) -> str | None:
    if not coords or kind not in ("point", "line", "polygon"):
        return None
    if kind == "point":
        lng, lat = coords[0]
        return f"POINT({lng} {lat})"
    if kind == "line":
        if len(coords) < 2:
            return None
        body = ", ".join(f"{lng} {lat}" for lng, lat in coords)
        return f"LINESTRING({body})"
    if len(coords) < 3:
        return None
    ring = list(coords)
    if ring[0] != ring[-1]:
        ring.append(ring[0])
    body = ", ".join(f"{lng} {lat}" for lng, lat in ring)
    return f"POLYGON(({body}))"


def _kind_for_coords(coords, column_kind, payload_kind) -> str | None:
    if column_kind in ("point", "line", "polygon"):
        return column_kind
    if payload_kind in ("point", "line", "polygon"):
        return payload_kind
    if len(coords) >= 3:
        return "polygon"
    if len(coords) >= 2:
        return "line"
    if len(coords) == 1:
        return "point"
    return None


def _wkt_from_geos(geom, column_kind) -> str | None:
    gtype = geom.geom_type or ""
    if column_kind == "point" and "Point" not in gtype:
        return None
    if column_kind == "line" and "Line" not in gtype:
        return None
    if column_kind == "polygon" and "Polygon" not in gtype:
        return None
    return geom.wkt


def parse_geometry(val, col_type: str) -> str:
    """
    Convert GeoJSON, WKT, a lat/lng pair, or mobile {points:[...]} capture
    into WKT that matches the column.

    A line or polygon payload must not be reduced to its first vertex.
    Generic geometry columns (mixed) keep the captured shape.
    """
    if val is None or val == "":
        return None
    column_kind = _column_geometry_kind(col_type)

    if isinstance(val, str):
        stripped = val.strip()
        if not stripped:
            return None
        if stripped[0] in "{[":
            try:
                return parse_geometry(json.loads(stripped), col_type)
            except json.JSONDecodeError:
                return None
        try:
            return _wkt_from_geos(GEOSGeometry(stripped), column_kind)
        except Exception:
            if "," in stripped and column_kind in ("point", "any"):
                try:
                    parts = [p.strip() for p in stripped.split(",")]
                    if len(parts) == 2:
                        lat, lng = float(parts[0]), float(parts[1])
                        return f"POINT({lng} {lat})"
                except ValueError:
                    return None
            return None

    if isinstance(val, (list, tuple)):
        coords = _coord_pairs(list(val))
        if not coords and len(val) == 2:
            try:
                coords = [(float(val[0]), float(val[1]))]
            except (TypeError, ValueError):
                return None
        return _wkt_for_kind(coords, _kind_for_coords(coords, column_kind, None))

    if isinstance(val, dict):
        nested = val.get("geometry")
        if isinstance(nested, dict) and nested is not val:
            parsed = parse_geometry(nested, col_type)
            if parsed:
                return parsed

        payload_kind = _payload_geometry_kind(val)
        points = val.get("points")
        if isinstance(points, list) and points:
            coords = _coord_pairs(points)
            wkt = _wkt_for_kind(
                coords, _kind_for_coords(coords, column_kind, payload_kind)
            )
            if wkt:
                return wkt

        if val.get("type") and "coordinates" in val:
            try:
                geom = GEOSGeometry(json.dumps(val))
                return _wkt_from_geos(geom, column_kind)
            except Exception:
                pass

        lat = val.get("latitude", val.get("lat"))
        lng = val.get("longitude", val.get("lng", val.get("lon")))
        if lat is not None and lng is not None:
            # A single vertex is a point. Do not use it to stand in for a
            # line or polygon that failed to include its vertices.
            if payload_kind in ("line", "polygon") or column_kind in (
                "line",
                "polygon",
            ):
                return None
            try:
                return f"POINT({float(lng)} {float(lat)})"
            except (TypeError, ValueError):
                return None
    return None


def _reject_date_answer(value, question_path: str) -> None:
    """Same failure as an invalid DATE insert: the whole submission rolls back."""
    shown = value if isinstance(value, str) else repr(value)
    raise DataError(
        f'invalid input syntax for type date: "{shown}" ({question_path})'
    )


def _split_date_parts(text: str, widths: tuple[int, ...]) -> tuple[str, ...]:
    parts = text.split("-")
    if len(parts) != len(widths):
        raise ValueError(text)
    if any(
        len(part) != width or not part.isdigit()
        for part, width in zip(parts, widths)
    ):
        raise ValueError(text)
    return tuple(parts)


def _date_without_time(text: str) -> str:
    """A time suffix starts with T or a space. Keep the date as written."""
    cut = len(text)
    for separator in ("T", " "):
        found = text.find(separator)
        if found != -1 and found < cut:
            cut = found
    return text[:cut]


def _iso_numbers(text: str, widths: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(int(part) for part in _split_date_parts(text, widths))


def _stored_month_year(prefix: str) -> str:
    """YYYY-MM, or a real YYYY-MM-DD, stored as the first of that month."""
    parts = prefix.split("-")
    if len(parts) == 2:
        year, month = _iso_numbers(prefix, (4, 2))
        parsed = date(year, month, 1)
    elif len(parts) == 3:
        year, month, day = _iso_numbers(prefix, (4, 2, 2))
        parsed = date(year, month, day)
    else:
        raise ValueError(prefix)
    return f"{parsed.year:04d}-{parsed.month:02d}-01"


def _stored_year(prefix: str) -> str:
    """YYYY, YYYY-MM, or a real YYYY-MM-DD, stored as 1 January."""
    parts = prefix.split("-")
    if len(parts) == 1:
        if len(prefix) != 4 or not prefix.isdigit():
            raise ValueError(prefix)
        parsed = date(int(prefix), 1, 1)
    elif len(parts) == 2:
        year, month = _iso_numbers(prefix, (4, 2))
        parsed = date(year, month, 1)
    elif len(parts) == 3:
        year, month, day = _iso_numbers(prefix, (4, 2, 2))
        parsed = date(year, month, day)
    else:
        raise ValueError(prefix)
    return f"{parsed.year:04d}-01-01"


def stored_date_for_format(value, date_format: str, question_path: str):
    """
    Map a mobile date answer onto the DATE column.

    Absent dateFormat and full_date are returned unchanged. Postgres accepts
    or rejects them, as it did before this attribute existed. month_year is
    stored as the first of that month, year as 1 January. A longer date, with
    or without a time, is shortened the same way so an older app is not refused.
    None and "" are left unchanged.
    """
    if value is None or value == "":
        return value
    if not date_format or date_format == "full_date":
        return value
    if not isinstance(value, str):
        _reject_date_answer(value, question_path)
    text = value.strip()
    if text == "":
        return value
    prefix = _date_without_time(text)
    try:
        if date_format == "month_year":
            return _stored_month_year(prefix)
        if date_format == "year":
            return _stored_year(prefix)
    except ValueError:
        _reject_date_answer(text, question_path)
    _reject_date_answer(text, question_path)


def _validate_collection_full_date(value, question_path: str) -> None:
    """Explicit full_date in JSON: a real YYYY-MM-DD, plus an optional time suffix."""
    if value is None or value == "":
        return
    if not isinstance(value, str):
        _reject_date_answer(value, question_path)
    text = value.strip()
    if text == "":
        return
    try:
        year, month, day = _iso_numbers(_date_without_time(text), (4, 2, 2))
        date(year, month, day)
    except ValueError:
        _reject_date_answer(text, question_path)


def display_date_for_format(value, date_format: str):
    """Show a stored DATE as the question's dateFormat."""
    parsed = _stored_date_value(value)
    if parsed is None:
        return value
    if date_format == "year":
        return f"{parsed.year:04d}"
    if date_format == "month_year":
        return f"{parsed.year:04d}-{parsed.month:02d}"
    return parsed.isoformat()


def _stored_date_value(value):
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        text = value.strip()
        if len(text) >= 10 and text[4] == "-" and text[7] == "-":
            try:
                return date.fromisoformat(text[:10])
            except ValueError:
                return None
    return None


def _date_answer_context(questions: list) -> tuple[dict, dict]:
    """Date column formats, and collection questions whose dates live in JSONB."""
    formats = {}
    collections = {}
    for question in walk_storage_questions(questions or []):
        q_id = question.get("id")
        if not q_id:
            continue
        q_type = (question.get("type") or "").lower()
        if q_type == "date":
            formats[q_id] = effective_date_format(question)
        elif q_type == "collection":
            collections[q_id] = question
    return formats, collections


def _validate_repeat_item(item: dict, questions: list, path: str) -> None:
    for question in questions or []:
        if not isinstance(question, dict):
            continue
        q_type = (question.get("type") or "").lower()
        q_id = question.get("id")
        nested = nested_questions(question)
        if q_type in ("section", "group", "note"):
            # Groups are layout. Child answers sit on the same repeat item.
            _validate_repeat_item(item, nested, path)
            continue
        if q_type == "collection" and q_id and q_id in item:
            _validate_repeat_list(item.get(q_id), nested, f"{path}.{q_id}")
            continue
        if q_type != "date" or not q_id or q_id not in item:
            continue
        # No dateFormat attribute at all: store the JSON as sent, with no date check.
        # effective_date_format would turn that absence into full_date.
        if "dateFormat" not in question:
            continue
        question_path = f"{path}.{q_id}"
        raw_format = question.get("dateFormat")
        if raw_format == "full_date":
            _validate_collection_full_date(item.get(q_id), question_path)
            continue
        # Check the shape, and leave the original string in the JSONB payload.
        stored_date_for_format(item.get(q_id), raw_format, question_path)


def _validate_repeat_list(value, questions: list, path: str) -> None:
    if value is None or value == "":
        return
    items = value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return
        try:
            items = json.loads(stripped)
        except json.JSONDecodeError:
            return
    if not isinstance(items, list):
        return
    for index, item in enumerate(items):
        if isinstance(item, dict):
            _validate_repeat_item(item, questions, f"{path}[{index}]")


def validate_collection_date_answers(value, collection_question: dict, path: str) -> None:
    """Reject a collection date that does not match its dateFormat.

    A date question with no dateFormat attribute is not checked. Valid values stay as sent.
    """
    _validate_repeat_list(value, nested_questions(collection_question), path)


@transaction.atomic
def sync_submission_to_physical_table_service(
    client_submission_id: str,
    device_id: str,
    form_version,
    answers: dict,
    user = None
) -> tuple[SubmissionIndex, bool]:
    """
    Syncs offline submission details securely into the generated PostGIS table
    and creates a SubmissionIndex metadata entry.
    
    Returns (submission_index_instance, is_duplicate).
    """
    form = form_version.form
    project = form.project
    
    # Enforce unique constraint check (prevent duplicate client_submission_id per device/form)
    existing = SubmissionIndex.objects.filter(
        device_id=device_id,
        client_submission_id=client_submission_id,
        form=form
    ).first()
    
    if existing:
        return existing, True

    write_version = get_live_submission_version(form, fallback=form_version)
    table_name = getattr(write_version, "physical_table_name", None) if write_version else None
    if not table_name:
        table_name = form_version.physical_table_name
        write_version = form_version
    if not table_name:
        raise ValidationError(f"Form version '{form_version.id}' does not have a physical table mapped.")

    # Write into the live published table so the submissions grid sees rows
    # from collectors still on an older downloaded version.
    column_mapping = {
        **(form_version.column_mapping or {}),
        **(getattr(write_version, "column_mapping", None) or {}),
    }
    live_cols = set(list_physical_table_columns(table_name))
    if live_cols:
        column_mapping = {
            q_id: col for q_id, col in column_mapping.items() if col in live_cols
        }

    questions = list((form_version.schema or {}).get("questions", []))
    if write_version is not None and write_version.id != form_version.id:
        questions.extend((write_version.schema or {}).get("questions", []))

    # Generate column types to parse geometry columns
    _, db_types = generate_column_mapping_service(questions)

    # Prefer the version the device downloaded. Its dateFormat is what it sent.
    live_formats, live_collections = {}, {}
    if write_version is not None:
        live_formats, live_collections = _date_answer_context(
            (write_version.schema or {}).get("questions", [])
        )
    device_formats, device_collections = _date_answer_context(
        (form_version.schema or {}).get("questions", [])
    )
    date_formats = {**live_formats, **device_formats}
    collection_questions = {**live_collections, **device_collections}

    submission_uuid = uuid.uuid4()
    synced_at = timezone.now()
    sync_status = 'synced'
    submitted_by_id = user.id if user else None
    
    # Execute insert in custom PostGIS table
    with connection.cursor() as cursor:
        cols = [
            'submission_uuid', 'project_id', 'form_id', 'form_version_id',
            'submitted_by_id', 'device_id', 'client_submission_id', 'sync_status', 'synced_at'
        ]
        vals = [
            str(submission_uuid), str(project.id), str(form.id), str(form_version.id),
            submitted_by_id, device_id, client_submission_id, sync_status, synced_at
        ]
        
        col_identifiers = [sql.Identifier(c) for c in cols]
        val_placeholders = [sql.Placeholder() for _ in cols]
        
        for q_id, val in answers.items():
            if q_id not in column_mapping:
                continue
                
            col_name = column_mapping[q_id]
            col_type = db_types.get(col_name, 'TEXT')

            if q_id in date_formats:
                val = stored_date_for_format(val, date_formats[q_id], q_id)
            elif q_id in collection_questions:
                validate_collection_date_answers(
                    val, collection_questions[q_id], q_id
                )

            col_identifiers.append(sql.Identifier(col_name))
            
            if "GEOMETRY" in col_type.upper():
                parsed_wkt = parse_geometry(val, col_type)
                if parsed_wkt:
                    val_placeholders.append(sql.SQL("ST_GeomFromText({}, 4326)").format(sql.Placeholder()))
                    vals.append(parsed_wkt)
                else:
                    val_placeholders.append(sql.SQL("NULL"))
            else:
                val_placeholders.append(sql.Placeholder())
                if isinstance(val, (dict, list)):
                    vals.append(json.dumps(val))
                else:
                    vals.append(val)
                    
        insert_query = sql.SQL("INSERT INTO {table_name} ({cols}) VALUES ({vals}) RETURNING id").format(
            table_name=sql.Identifier(table_name),
            cols=sql.SQL(", ").join(col_identifiers),
            vals=sql.SQL(", ").join(val_placeholders)
        )
        
        cursor.execute(insert_query, vals)
        row_id = cursor.fetchone()[0]
        
    # Create the index entry
    submission_index = SubmissionIndex.objects.create(
        project=project,
        form=form,
        form_version=form_version,
        submitted_by=user,
        device_id=device_id,
        client_submission_id=client_submission_id,
        physical_table_name=table_name,
        physical_row_id=row_id,
        sync_status=sync_status,
        synced_at=synced_at
    )
    
    return submission_index, False


def copy_missing_submissions_to_live_table(form) -> int:
    """
    Copy rows that still live only on older version tables into the live
    submissions table, and retarget SubmissionIndex at the new row ids.
    """
    live_table = form.submission_table_name
    if not live_table or not physical_table_exists(live_table):
        return 0

    live_cols = list_physical_table_columns(live_table)
    if "submission_uuid" not in live_cols:
        return 0

    copied = 0
    versions = form.versions.exclude(physical_table_name__isnull=True).exclude(
        physical_table_name=""
    )
    for version in versions:
        old_table = version.physical_table_name
        if not old_table or old_table == live_table:
            continue
        if not physical_table_exists(old_table):
            continue
        old_cols = set(list_physical_table_columns(old_table))
        copy_cols = [col for col in live_cols if col != "id" and col in old_cols]
        if "submission_uuid" not in copy_cols:
            continue

        insert_cols = sql.SQL(", ").join(sql.Identifier(c) for c in copy_cols)
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL(
                    """
                    INSERT INTO {live} ({cols})
                    SELECT {cols}
                    FROM {old} AS src
                    WHERE NOT EXISTS (
                        SELECT 1 FROM {live} AS dest
                        WHERE dest.submission_uuid = src.submission_uuid
                    )
                    RETURNING submission_uuid, id
                    """
                ).format(
                    live=sql.Identifier(live_table),
                    old=sql.Identifier(old_table),
                    cols=insert_cols,
                )
            )
            new_rows = cursor.fetchall()

        if new_rows:
            uuid_to_new_id = {str(sub_uuid): new_id for sub_uuid, new_id in new_rows}
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL(
                        "SELECT id, submission_uuid FROM {old} WHERE submission_uuid IN ({uuids})"
                    ).format(
                        old=sql.Identifier(old_table),
                        uuids=sql.SQL(", ").join(
                            sql.Placeholder() for _ in uuid_to_new_id
                        ),
                    ),
                    list(uuid_to_new_id.keys()),
                )
                old_id_rows = cursor.fetchall()

            for old_id, sub_uuid in old_id_rows:
                new_id = uuid_to_new_id.get(str(sub_uuid))
                if new_id is None:
                    continue
                SubmissionIndex.objects.filter(
                    form=form,
                    physical_table_name=old_table,
                    physical_row_id=old_id,
                ).update(
                    physical_table_name=live_table,
                    physical_row_id=new_id,
                )
            copied += len(new_rows)

        # Publish already copies rows into the new table and leaves
        # SubmissionIndex on the old table. Point those at the live row
        # so the detail drawer opens the same record the grid shows.
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL(
                    """
                    SELECT src.id, dest.id
                    FROM {old} AS src
                    INNER JOIN {live} AS dest
                        ON dest.submission_uuid = src.submission_uuid
                    """
                ).format(
                    old=sql.Identifier(old_table),
                    live=sql.Identifier(live_table),
                )
            )
            already_live = cursor.fetchall()

        for old_id, live_id in already_live:
            SubmissionIndex.objects.filter(
                form=form,
                physical_table_name=old_table,
                physical_row_id=old_id,
            ).update(
                physical_table_name=live_table,
                physical_row_id=live_id,
            )
    return copied
