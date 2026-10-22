import uuid
import json
from django.db import transaction, connection
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
