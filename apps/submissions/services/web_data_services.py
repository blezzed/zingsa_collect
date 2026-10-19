import json
import logging
from django.db import connection, transaction
from django.contrib.gis.geos import GEOSGeometry
from psycopg2 import sql

from apps.forms.services.form_services import (
    get_live_submission_version,
    list_physical_table_columns,
    physical_geometry_columns,
    physical_table_exists,
)
from apps.forms.services.question_schema import (
    SPATIAL_QUESTION_TYPES,
    collection_question_columns,
    nested_questions,
    walk_all_questions,
    walk_storage_questions,
)
from common.media_url_rewrite import rewrite_media_urls_in_data
from apps.submissions.services.submission_services import (
    copy_missing_submissions_to_live_table,
)

logger = logging.getLogger(__name__)


def _ensure_live_submissions(form) -> None:
    try:
        copy_missing_submissions_to_live_table(form)
    except Exception:
        logger.exception(
            "Could not copy older-version submissions into the live table"
        )


def _is_geojson_geometry(value) -> bool:
    return (
        isinstance(value, dict)
        and value.get("type") in {
            "Point",
            "MultiPoint",
            "LineString",
            "MultiLineString",
            "Polygon",
            "MultiPolygon",
            "GeometryCollection",
        }
        and "coordinates" in value
    )


def _lat_lng_coord(node):
    """Return [lng, lat] from a dict, or None."""
    if not isinstance(node, dict):
        return None
    lat = node.get("latitude", node.get("lat"))
    lng = node.get("longitude", node.get("lng", node.get("lon")))
    if lat is None or lng is None:
        return None
    try:
        return [float(lng), float(lat)]
    except (TypeError, ValueError):
        return None


def _coords_from_point_list(points):
    coords = []
    if not isinstance(points, list):
        return coords
    for item in points:
        pair = _lat_lng_coord(item)
        if pair:
            coords.append(pair)
    return coords


def _geometry_from_coords(coords, expected_type=None):
    """
    Build GeoJSON from vertex coords using the form field type when available.
    Mobile polygon/line capture stores vertices as {points:[{latitude,longitude},...]}.
    """
    if not coords:
        return None
    et = (expected_type or "").lower()

    if et == "polygon" or (et == "geometry" and len(coords) >= 3):
        if len(coords) < 3:
            return None
        ring = list(coords)
        if ring[0] != ring[-1]:
            ring.append(list(ring[0]))
        return {"type": "Polygon", "coordinates": [ring]}

    if et == "line" or (et == "geometry" and len(coords) >= 2):
        if len(coords) < 2:
            return None
        return {"type": "LineString", "coordinates": coords}

    if et in ("location", "point"):
        return {"type": "Point", "coordinates": coords[0]}

    # Infer when schema type is missing (deep-scan fallback)
    if len(coords) >= 3:
        ring = list(coords)
        if ring[0] != ring[-1]:
            ring.append(list(ring[0]))
        return {"type": "Polygon", "coordinates": [ring]}
    if len(coords) == 2:
        return {"type": "LineString", "coordinates": coords}
    return {"type": "Point", "coordinates": coords[0]}


def _coerce_to_geojson(value, expected_type=None):
    """Normalize stored collection/group spatial values into a GeoJSON geometry dict."""
    if value is None or value == "":
        return None

    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            try:
                value = json.loads(stripped)
            except (json.JSONDecodeError, TypeError):
                value = stripped
        else:
            # "lat, lng" or WKT
            if "," in stripped and not stripped.upper().startswith(
                ("POINT", "LINE", "POLYGON", "MULTI")
            ):
                try:
                    parts = [p.strip() for p in stripped.split(",")]
                    if len(parts) == 2:
                        lat, lng = float(parts[0]), float(parts[1])
                        return {
                            "type": "Point",
                            "coordinates": [lng, lat],
                        }
                except ValueError:
                    pass
            # Only attempt GEOS on values that look like WKT/EWKT/hex EWKB.
            # Random answer strings must not hit GEOS (it logs ERROR on every miss).
            upper = stripped.upper()
            looks_wkt = upper.startswith(
                (
                    "POINT",
                    "LINESTRING",
                    "POLYGON",
                    "MULTI",
                    "GEOMETRYCOLLECTION",
                    "SRID=",
                )
            )
            looks_hex = len(stripped) >= 18 and all(
                c in "0123456789abcdefABCDEF" for c in stripped
            )
            if looks_wkt or looks_hex:
                try:
                    geom = GEOSGeometry(stripped)
                    return json.loads(geom.geojson)
                except Exception:
                    return None
            return None

    if isinstance(value, (list, tuple)):
        # Mobile may store vertices as a bare list of {lat,lng}
        if value and isinstance(value[0], dict):
            if value[0].get("type") == "Feature":
                return _coerce_to_geojson(
                    {"type": "FeatureCollection", "features": list(value)},
                    expected_type=expected_type,
                )
            coords = _coords_from_point_list(value)
            if coords:
                return _geometry_from_coords(coords, expected_type)
        if value and isinstance(value[0], (list, tuple)):
            coords = []
            for item in value:
                try:
                    coords.append([float(item[0]), float(item[1])])
                except (TypeError, ValueError, IndexError):
                    coords = []
                    break
            if coords:
                return _geometry_from_coords(coords, expected_type)
        if len(value) == 2:
            try:
                a, b = float(value[0]), float(value[1])
                return {"type": "Point", "coordinates": [a, b]}
            except (TypeError, ValueError):
                return None

    if isinstance(value, dict):
        if value.get("type") == "Feature" and isinstance(value.get("geometry"), dict):
            return _coerce_to_geojson(value["geometry"], expected_type=expected_type)
        if value.get("type") == "FeatureCollection" and isinstance(value.get("features"), list):
            geoms = []
            for feature in value["features"]:
                if not isinstance(feature, dict):
                    continue
                geom = _coerce_to_geojson(feature.get("geometry"), expected_type=expected_type)
                if geom:
                    geoms.append(geom)
            if len(geoms) == 1:
                return geoms[0]
            if len(geoms) > 1:
                return {"type": "GeometryCollection", "geometries": geoms}
            return None
        if value.get("type") == "GeometryCollection" and isinstance(value.get("geometries"), list):
            return {
                "type": "GeometryCollection",
                "geometries": value["geometries"],
            }
        if _is_geojson_geometry(value):
            return {
                "type": value["type"],
                "coordinates": value["coordinates"],
            }
        # Mobile polygon / line: { points: [{latitude, longitude}, ...], timestamp }
        points = value.get("points")
        if isinstance(points, list) and points:
            coords = _coords_from_point_list(points)
            geom = _geometry_from_coords(coords, expected_type)
            if geom:
                return geom
        lat = value.get("latitude", value.get("lat"))
        lng = value.get("longitude", value.get("lng", value.get("lon")))
        if lat is not None and lng is not None:
            try:
                return {
                    "type": "Point",
                    "coordinates": [float(lng), float(lat)],
                }
            except (TypeError, ValueError):
                return None

    return None


def _feature_key(props: dict) -> str:
    """Stable id for one map feature (submission + field + repeat)."""
    row_id = props.get("id")
    field = props.get("field") or props.get("collection_field") or "geom"
    repeat = props.get("repeat_index")
    repeat_part = "root" if repeat is None else str(repeat)
    source = props.get("source") or "submission"
    return f"{row_id}:{source}:{field}:{repeat_part}"


def _extract_spatial_from_schema(
    questions: list,
    answers: dict,
    base_props: dict,
    out: list,
):
    """
    Walk group/collection schema against an answers dict and collect geometries.
    Groups are layout-only (children share the same answers object).
    Collections nest repeat items keyed by child question ids.
    """
    if not isinstance(answers, dict):
        return

    for q in questions:
        if not isinstance(q, dict):
            continue
        q_type = (q.get("type") or "").lower()
        q_id = q.get("id")
        nested = nested_questions(q)
        label = q.get("label") or q_id

        if q_type in ("section", "group", "note") and nested:
            nested_props = base_props
            if q_type == "group" and q_id:
                nested_props = {
                    **base_props,
                    "group": q_id,
                    "group_label": label,
                }
            _extract_spatial_from_schema(nested, answers, nested_props, out)
            continue

        if q_type == "collection":
            raw = answers.get(q_id)
            items = raw if isinstance(raw, list) else []
            for repeat_index, item in enumerate(items):
                if not isinstance(item, dict):
                    continue
                _extract_spatial_from_schema(
                    nested,
                    item,
                    {
                        **base_props,
                        "collection": q_id,
                        "collection_label": label,
                        "repeat_index": repeat_index,
                        "source": "collection",
                    },
                    out,
                )
            continue

        if q_type in SPATIAL_QUESTION_TYPES and q_id:
            geom = _coerce_to_geojson(answers.get(q_id), expected_type=q_type)
            if not geom:
                continue
            props = {
                **base_props,
                "field": q_id,
                "field_label": label,
                "question_type": q_type,
                "source": base_props.get("source") or "submission",
            }
            if "collection" in base_props:
                props["collection_field"] = q_id
            props["feature_key"] = _feature_key(props)
            out.append((geom, props))


def _looks_spatial_value(value) -> bool:
    """True when a nested value is worth feeding to geometry coerce/deep-scan."""
    if value is None or value == "":
        return False
    if isinstance(value, (list, tuple)):
        if not value:
            return False
        if isinstance(value[0], dict):
            return True
        if len(value) == 2:
            try:
                float(value[0])
                float(value[1])
                return True
            except (TypeError, ValueError):
                return False
        return False
    if isinstance(value, dict):
        if _is_geojson_geometry(value):
            return True
        if isinstance(value.get("points"), list):
            return True
        if value.get("latitude", value.get("lat")) is not None and value.get(
            "longitude", value.get("lng", value.get("lon"))
        ) is not None:
            return True
        return False
    if isinstance(value, str):
        stripped = value.strip()
        upper = stripped.upper()
        if upper.startswith(
            (
                "POINT",
                "LINESTRING",
                "POLYGON",
                "MULTI",
                "GEOMETRYCOLLECTION",
                "SRID=",
            )
        ):
            return True
        if stripped.startswith("{") or stripped.startswith("["):
            return True
    return False


def _geometries_from_repeat_payload(repeat_items, base_props, collection_question=None):
    """
    Extract GeoJSON geometries from a collection repeat array.
    Prefer schema-aware walk when collection_question is provided; otherwise
    fall back to a deep scan of nested objects.
    """
    features = []
    if collection_question is not None:
        items = repeat_items if isinstance(repeat_items, list) else []
        synthetic = {collection_question.get("id"): items}
        _extract_spatial_from_schema(
            [collection_question],
            synthetic,
            base_props,
            features,
        )
        if features:
            return features
        # Schema walk found nothing — only deep-scan spatial-looking values
        # (never feed every text/radio answer into GEOS).

    if not isinstance(repeat_items, list):
        return features

    def deep_scan(node, props, path=""):
        if isinstance(node, list):
            for idx, child in enumerate(node):
                deep_scan(child, {**props, "repeat_index": props.get("repeat_index", idx)}, f"{path}[{idx}]")
            return
        if not isinstance(node, dict):
            return
        # Prefer whole-node coerce (e.g. {points:[...]} polygon) before
        # descending into vertex keys like "points".
        expected = props.get("_expected_type")
        geom = _coerce_to_geojson(node, expected_type=expected)
        if geom and props.get("_from_field"):
            item_props = {
                k: v for k, v in props.items() if not k.startswith("_")
            }
            item_props.setdefault("field", props.get("_from_field"))
            item_props.setdefault("field_label", props.get("_from_field"))
            if expected:
                item_props.setdefault("question_type", expected)
            item_props["feature_key"] = _feature_key(item_props)
            features.append((geom, item_props))
            return
        for key, val in node.items():
            # Skip raw vertex arrays once parent spatial payload is handled above
            if key == "points" and isinstance(val, list):
                continue
            if not _looks_spatial_value(val):
                continue
            coerced = _coerce_to_geojson(val, expected_type=expected)
            if coerced:
                item_props = {
                    **{k: v for k, v in props.items() if not k.startswith("_")},
                    "collection_field": key,
                    "field": key,
                    "field_label": props.get("field_label") or key,
                    "source": "collection",
                }
                if expected:
                    item_props.setdefault("question_type", expected)
                item_props["feature_key"] = _feature_key(item_props)
                features.append((coerced, item_props))
            elif isinstance(val, (dict, list)):
                deep_scan(val, {**props, "_from_field": key}, f"{path}.{key}")

    for repeat_index, item in enumerate(repeat_items):
        deep_scan(
            item,
            {**base_props, "repeat_index": repeat_index, "source": "collection"},
        )
    return features


def _parse_stored_json(value):
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    return None


def _live_form_version(form):
    """Published tip that owns the submissions table the dashboard reads."""
    return get_live_submission_version(form) or form.current_version


def _schema_geometry_columns(version) -> list[dict]:
    """Spatial storage columns declared on a form version."""
    found = []
    seen = set()
    if not version or not version.column_mapping:
        return found
    questions = (version.schema or {}).get("questions") or []

    def walk(nodes, group_id=None, group_label=None):
        for question in nodes or []:
            if not isinstance(question, dict):
                continue
            q_type = (question.get("type") or "").lower()
            q_id = question.get("id")
            nested = nested_questions(question)
            label = question.get("label") or q_id
            if q_type == "collection":
                continue
            if q_type in ("section", "group", "note") and nested:
                next_group = (group_id, group_label)
                if q_type == "group" and q_id:
                    next_group = (q_id, label)
                walk(nested, next_group[0], next_group[1])
                continue
            if q_type not in SPATIAL_QUESTION_TYPES or not q_id:
                continue
            if q_id not in version.column_mapping:
                continue
            col = version.column_mapping[q_id]
            if col in seen:
                continue
            seen.add(col)
            found.append({
                "col": col,
                "qid": q_id,
                "label": label,
                "qtype": q_type,
                "group_id": group_id,
                "group_label": group_label,
            })

    walk(questions)
    return found


def _with_physical_geometry_columns(table_name: str, columns: list[dict]) -> list[dict]:
    """Include PostGIS columns the schema walk missed (map-feature ``geom``)."""
    seen = {item["col"] for item in columns}
    for col in physical_geometry_columns(table_name):
        if col in seen:
            continue
        seen.add(col)
        columns.append({
            "col": col,
            "qid": col,
            "label": "Map feature" if col in ("geom", "map_feature") else col,
            "qtype": "geometry",
            "group_id": None,
            "group_label": None,
        })
    return columns


def _geometry_feature(row_id, geom_json, meta: dict):
    if not isinstance(geom_json, dict) or "type" not in geom_json:
        return None
    props = {
        "id": row_id,
        "field": meta["qid"],
        "field_label": meta["label"],
        "question_type": meta["qtype"],
        "source": "submission",
    }
    if meta.get("group_id"):
        props["group"] = meta["group_id"]
        props["group_label"] = meta["group_label"]
    props["feature_key"] = _feature_key(props)
    return {
        "type": "Feature",
        "geometry": geom_json,
        "properties": props,
    }


def _parse_geom_json(raw, expected_type=None):
    if raw in (None, ""):
        return None
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = raw
    else:
        parsed = raw
    if isinstance(parsed, dict) and parsed.get("type") and (
        "coordinates" in parsed or "geometries" in parsed
    ):
        return parsed
    return _coerce_to_geojson(parsed, expected_type=expected_type)


def _fetch_geojson_rows(table_name: str, geom_columns: list[dict], collection_cols: list):
    """
    Read id, geometry, and collection payloads.

    A failed statement rolls back to a savepoint so one bad column does not
    abort the request and hide every feature.
    """
    postgis_names = set(physical_geometry_columns(table_name))
    select_parts = [sql.Identifier("id")]
    for meta in geom_columns:
        col = sql.Identifier(meta["col"])
        if meta["col"] in postgis_names or not postgis_names:
            select_parts.append(
                sql.SQL(
                    "CASE WHEN {c} IS NULL THEN NULL ELSE ST_AsGeoJSON({c}) END"
                ).format(c=col)
            )
        else:
            select_parts.append(col)
    for _, col in collection_cols:
        select_parts.append(sql.Identifier(col))

    query = sql.SQL("SELECT {cols} FROM {table}").format(
        cols=sql.SQL(", ").join(select_parts),
        table=sql.Identifier(table_name),
    )
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchall()
    except Exception:
        logger.exception("GeoJSON query failed for table %s", table_name)

    # Retry column by column so one non-geometry field cannot blank the map.
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL("SELECT id FROM {} ORDER BY id").format(
                        sql.Identifier(table_name)
                    )
                )
                ids = [row[0] for row in cursor.fetchall()]
    except Exception:
        logger.exception("Could not list submission ids for %s", table_name)
        return []

    width = 1 + len(geom_columns) + len(collection_cols)
    by_id = {row_id: [row_id] + [None] * (width - 1) for row_id in ids}

    def _fill(sql_expr, index) -> bool:
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(sql_expr)
                    pairs = cursor.fetchall()
        except Exception:
            logger.exception("Skipping unreadable column on %s", table_name)
            return False
        for row_id, value in pairs:
            slot = by_id.get(row_id)
            if slot is not None:
                slot[index] = value
        return True

    for index, meta in enumerate(geom_columns):
        col = sql.Identifier(meta["col"])
        read_as_geojson = _fill(
            sql.SQL(
                "SELECT id, CASE WHEN {c} IS NULL THEN NULL ELSE ST_AsGeoJSON({c}) END FROM {t}"
            ).format(c=col, t=sql.Identifier(table_name)),
            1 + index,
        )
        if not read_as_geojson:
            _fill(
                sql.SQL("SELECT id, {c} FROM {t}").format(
                    c=col, t=sql.Identifier(table_name)
                ),
                1 + index,
            )
    for index, (_, col_name) in enumerate(collection_cols):
        _fill(
            sql.SQL("SELECT id, {c} FROM {t}").format(
                c=sql.Identifier(col_name),
                t=sql.Identifier(table_name),
            ),
            1 + len(geom_columns) + index,
        )
    return [by_id[row_id] for row_id in ids]


def _supplement_features_from_older_tables(form, live_table: str, features: list) -> list:
    """
    Draw features that still live on a previous version table.

    Republishing a map-first form used to drop the geometry column, so the
    live row kept its attributes and lost the shape. The map uses the live
    row id so it still lines up with View Submissions.
    """
    featured_ids = {
        feature.get("properties", {}).get("id")
        for feature in features
        if isinstance(feature, dict)
    }
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL("SELECT id, submission_uuid FROM {}").format(
                        sql.Identifier(live_table)
                    )
                )
                live_rows = cursor.fetchall()
    except Exception:
        logger.exception("Could not read submission ids from %s", live_table)
        return features

    missing = {}
    for row_id, sub_uuid in live_rows:
        if row_id not in featured_ids and sub_uuid is not None:
            missing[str(sub_uuid)] = row_id
    if not missing:
        return features

    versions = sorted(
        form.versions.all(),
        key=lambda version: version.version_number or 0,
        reverse=True,
    )
    for version in versions:
        old_table = version.physical_table_name
        if (
            not old_table
            or old_table == live_table
            or not physical_table_exists(old_table)
            or not missing
        ):
            continue
        columns = _with_physical_geometry_columns(
            old_table, _schema_geometry_columns(version)
        )
        postgis_names = set(physical_geometry_columns(old_table))
        columns = [meta for meta in columns if meta["col"] in postgis_names]
        if not columns:
            continue
        uuids = list(missing.keys())
        select_parts = [sql.Identifier("submission_uuid")]
        for meta in columns:
            select_parts.append(
                sql.SQL(
                    "CASE WHEN {c} IS NULL THEN NULL ELSE ST_AsGeoJSON({c}) END"
                ).format(c=sql.Identifier(meta["col"]))
            )
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(
                        sql.SQL(
                            "SELECT {cols} FROM {table} WHERE submission_uuid IN ({uuids})"
                        ).format(
                            cols=sql.SQL(", ").join(select_parts),
                            table=sql.Identifier(old_table),
                            uuids=sql.SQL(", ").join(sql.Placeholder() for _ in uuids),
                        ),
                        uuids,
                    )
                    old_rows = cursor.fetchall()
        except Exception:
            logger.exception("Could not read older geometries from %s", old_table)
            continue
        for row in old_rows:
            sub_uuid = str(row[0])
            live_id = missing.get(sub_uuid)
            if live_id is None:
                continue
            found = False
            for index, raw in enumerate(row[1:]):
                feature = _geometry_feature(
                    live_id,
                    _parse_geom_json(raw, columns[index]["qtype"]),
                    columns[index],
                )
                if feature:
                    features.append(feature)
                    found = True
            if found:
                missing.pop(sub_uuid, None)
    return features


def get_web_geojson_service(form, user=None) -> dict:
    """
    Returns geometries from the physical table for map rendering.
    Includes:
    - top-level geometry columns (including those under groups/sections)
    - the map-first feature column, even when a later draft dropped it
    - GeoJSON / lat-lng values nested inside collection (JSONB) repeats,
      including spatial fields nested under groups within a collection item
    """
    _ensure_live_submissions(form)
    version = _live_form_version(form)
    table_name = form.submission_table_name or getattr(version, "physical_table_name", None)
    if not table_name:
        return {"type": "FeatureCollection", "features": []}

    existing = set(list_physical_table_columns(table_name))
    geom_columns = [
        meta
        for meta in _with_physical_geometry_columns(
            table_name, _schema_geometry_columns(version)
        )
        if meta["col"] in existing
    ]
    collection_cols = [
        pair
        for pair in collection_question_columns(version)
        if pair[1] in existing
    ]

    features = []
    if geom_columns or collection_cols:
        rows = _fetch_geojson_rows(table_name, geom_columns, collection_cols)
        for row in rows:
            row_id = row[0]
            base_props = {"id": row_id}

            for index, raw in enumerate(row[1:1 + len(geom_columns)]):
                feature = _geometry_feature(
                    row_id,
                    _parse_geom_json(raw, geom_columns[index]["qtype"]),
                    geom_columns[index],
                )
                if feature:
                    features.append(feature)

            collection_start = 1 + len(geom_columns)
            for index, (collection_q, _col_name) in enumerate(collection_cols):
                payload = _parse_stored_json(row[collection_start + index])
                if payload is None:
                    continue
                collection_id = collection_q.get("id")
                for geom_json, props in _geometries_from_repeat_payload(
                    payload,
                    {
                        **base_props,
                        "collection": collection_id,
                        "collection_label": collection_q.get("label") or collection_id,
                        "source": "collection",
                    },
                    collection_question=collection_q,
                ):
                    features.append({
                        "type": "Feature",
                        "geometry": geom_json,
                        "properties": props,
                    })

    features = _supplement_features_from_older_tables(form, table_name, features)
    return {"type": "FeatureCollection", "features": features}


def get_web_columns_service(form) -> list:
    """
    Returns column metadata for the frontend attribute table.
    """
    version = _live_form_version(form)
    if not version or not version.column_mapping:
        return []

    columns = [
        {"id": "id", "label": "ID", "type": "number"},
        {"id": "submission_uuid", "label": "Submission UUID", "type": "text"},
        {"id": "synced_at", "label": "Synced At", "type": "datetime"},
    ]

    for q in walk_storage_questions(version.schema.get("questions", [])):
        q_type = (q.get("type") or "").lower()
        if q_type in SPATIAL_QUESTION_TYPES:
            continue
        col_name = version.column_mapping.get(q["id"])
        if col_name:
            columns.append({
                "id": col_name,
                "label": q.get("label", q["id"]),
                "type": q.get("type", "text"),
            })

    return columns


def get_web_paginated_data_service(
    form,
    page: int,
    limit: int,
    user=None,
    search: str | None = None,
) -> dict:
    """
    Returns paginated tabular data, EXCLUDING heavy geometry strings
    so the grid loads extremely fast.

    Optional ``search`` filters rows with case-insensitive substring match
    across all non-geometry columns (backend pagination + filter).
    """
    _ensure_live_submissions(form)
    table_name = form.submission_table_name
    if not table_name:
        return {"data": [], "total": 0, "page": page, "limit": limit}

    offset = (page - 1) * limit
    version = _live_form_version(form)
    search_term = (search or "").strip()

    with connection.cursor() as cursor:
        cursor.execute(sql.SQL("SELECT * FROM {} LIMIT 0").format(sql.Identifier(table_name)))
        all_columns = [desc[0] for desc in cursor.description]

        geom_cols = []
        if version and version.column_mapping:
            for q in walk_all_questions(version.schema.get("questions", [])):
                if q.get("type") in SPATIAL_QUESTION_TYPES and q.get("id") in version.column_mapping:
                    geom_cols.append(version.column_mapping[q["id"]])

        safe_columns = [col for col in all_columns if col not in geom_cols]
        if not safe_columns:
            safe_columns = ["id"]

        where_sql = sql.SQL("")
        where_params: list = []
        if search_term:
            like = f"%{search_term}%"
            clauses = [
                sql.SQL("CAST({col} AS TEXT) ILIKE %s").format(col=sql.Identifier(col))
                for col in safe_columns
            ]
            where_sql = sql.SQL(" WHERE ({})").format(sql.SQL(" OR ").join(clauses))
            where_params = [like] * len(safe_columns)

        count_query = sql.SQL("SELECT COUNT(*) FROM {table}{where}").format(
            table=sql.Identifier(table_name),
            where=where_sql,
        )
        cursor.execute(count_query, where_params)
        total_rows = cursor.fetchone()[0]

        col_identifiers = [sql.Identifier(c) for c in safe_columns]
        query = sql.SQL(
            "SELECT {cols} FROM {table}{where} ORDER BY id DESC LIMIT %s OFFSET %s"
        ).format(
            cols=sql.SQL(", ").join(col_identifiers),
            table=sql.Identifier(table_name),
            where=where_sql,
        )

        cursor.execute(query, [*where_params, limit, offset])
        rows = cursor.fetchall()

        results = []
        for row in rows:
            row_dict = {}
            for col, val in zip(safe_columns, row):
                if isinstance(val, str) and val.startswith(("{", "[")):
                    try:
                        row_dict[col] = json.loads(val)
                    except Exception:
                        row_dict[col] = val
                else:
                    row_dict[col] = val
            results.append(rewrite_media_urls_in_data(row_dict))

    return {
        "data": results,
        "total": total_rows,
        "page": page,
        "limit": limit,
        "search": search_term,
    }


def _spatial_column_names(version) -> list:
    cols = []
    if not version or not version.column_mapping:
        return cols
    for q in walk_all_questions(version.schema.get("questions", [])):
        if q.get("type") in SPATIAL_QUESTION_TYPES and q.get("id") in version.column_mapping:
            col = version.column_mapping[q["id"]]
            if col not in cols:
                cols.append(col)
    return cols


def _serialize_cell(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, default=str)
    return value


def get_web_export_table_service(form) -> dict:
    """
    Full attribute table for export (no geometry WKT/GeoJSON columns).
    Collections remain as JSON in the main sheet; also returns parsed collection sheets.
    """
    _ensure_live_submissions(form)
    table_name = form.submission_table_name
    version = _live_form_version(form)
    empty = {
        "headers": [],
        "rows": [],
        "collections": [],
        "labels": [],
    }
    if not table_name or not version or not version.column_mapping:
        return empty

    geom_cols = set(_spatial_column_names(version))
    storage_qs = list(walk_storage_questions(version.schema.get("questions", [])))

    main_headers = [
        {"id": "id", "label": "ID", "type": "number"},
        {"id": "submission_uuid", "label": "Submission UUID", "type": "text"},
        {"id": "synced_at", "label": "Synced At", "type": "datetime"},
    ]
    collection_defs = []
    for q in storage_qs:
        q_type = (q.get("type") or "").lower()
        col = version.column_mapping.get(q["id"])
        if not col or col in geom_cols:
            continue
        entry = {
            "id": col,
            "label": q.get("label", q["id"]),
            "type": q.get("type", "text"),
            "question_id": q["id"],
        }
        main_headers.append(entry)
        if q_type == "collection":
            nested = nested_questions(q)
            child_headers = []
            for child in nested:
                if not isinstance(child, dict):
                    continue
                child_type = (child.get("type") or "").lower()
                if child_type in SPATIAL_QUESTION_TYPES:
                    continue
                if child_type in ("section", "group", "note"):
                    for grand in nested_questions(child):
                        if not isinstance(grand, dict):
                            continue
                        gt = (grand.get("type") or "").lower()
                        if gt in SPATIAL_QUESTION_TYPES or gt in (
                            "section",
                            "group",
                            "note",
                            "collection",
                        ):
                            continue
                        child_headers.append({
                            "id": grand.get("id"),
                            "label": grand.get("label", grand.get("id")),
                        })
                    continue
                if child_type == "collection":
                    continue
                child_headers.append({
                    "id": child.get("id"),
                    "label": child.get("label", child.get("id")),
                })
            collection_defs.append({
                "column": col,
                "question_id": q["id"],
                "label": q.get("label", q["id"]),
                "item_label": q.get("itemLabel") or "Item",
                "children": child_headers,
            })

    header_ids = [h["id"] for h in main_headers]
    labels = [
        {
            "name": h["id"],
            "label": h["label"],
            "type": h.get("type", "text"),
        }
        for h in main_headers
    ]

    with connection.cursor() as cursor:
        cursor.execute(sql.SQL("SELECT * FROM {} LIMIT 0").format(sql.Identifier(table_name)))
        all_columns = [desc[0] for desc in cursor.description]
        select_cols = [c for c in all_columns if c not in geom_cols]
        if not select_cols:
            select_cols = ["id"]

        query = sql.SQL("SELECT {cols} FROM {table} ORDER BY id ASC").format(
            cols=sql.SQL(", ").join(sql.Identifier(c) for c in select_cols),
            table=sql.Identifier(table_name),
        )
        cursor.execute(query)
        raw_rows = cursor.fetchall()

    rows = []
    collection_sheets = {
        d["question_id"]: {
            "label": d["label"],
            "headers": [
                {"id": "_parent_id", "label": "Parent ID"},
                {"id": "_index", "label": "Item index"},
                *[
                    {"id": c["id"], "label": c["label"]}
                    for c in d["children"]
                ],
            ],
            "rows": [],
        }
        for d in collection_defs
    }

    for raw in raw_rows:
        record = {}
        for col, val in zip(select_cols, raw):
            if isinstance(val, str) and val.startswith(("{", "[")):
                try:
                    record[col] = json.loads(val)
                except Exception:
                    record[col] = val
            else:
                record[col] = val

        row_out = []
        for hid in header_ids:
            value = record.get(hid)
            # Keep collection as JSON string in main sheet (Kobo main export style)
            row_out.append(_serialize_cell(value))
        rows.append(row_out)

        for cdef in collection_defs:
            payload = record.get(cdef["column"])
            items = payload if isinstance(payload, list) else []
            sheet = collection_sheets[cdef["question_id"]]
            for index, item in enumerate(items):
                if not isinstance(item, dict):
                    continue
                sheet_row = [
                    record.get("id"),
                    index + 1,
                ]
                for child in cdef["children"]:
                    sheet_row.append(_serialize_cell(item.get(child["id"])))
                sheet["rows"].append(sheet_row)

    return {
        "headers": main_headers,
        "rows": rows,
        "collections": list(collection_sheets.values()),
        "labels": labels,
        "slug": getattr(form, "slug", None) or str(form.id),
        "title": getattr(form, "title", None) or "export",
    }


def _escape_xml(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _sheet_xml(name: str, headers: list, rows: list) -> str:
    cols = len(headers)
    header_cells = "".join(
        f'<c t="inlineStr"><is><t>{_escape_xml(h["label"])}</t></is></c>'
        for h in headers
    )
    body = [f"<row r=\"1\">{header_cells}</row>"]
    for r_idx, row in enumerate(rows, start=2):
        cells = []
        for c_idx in range(cols):
            val = row[c_idx] if c_idx < len(row) else ""
            if val is None:
                val = ""
            cells.append(
                f'<c t="inlineStr"><is><t>{_escape_xml(val)}</t></is></c>'
            )
        body.append(f'<row r="{r_idx}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{''.join(body)}</sheetData></worksheet>"
    )


def build_xlsx_bytes(export_table: dict) -> bytes:
    """Minimal XLSX (OOXML) writer — main sheet + one sheet per collection."""
    import zipfile
    from io import BytesIO

    sheets = [
        ("Submissions", export_table["headers"], export_table["rows"]),
    ]
    used_names = {"Submissions"}
    for coll in export_table.get("collections") or []:
        base = (coll.get("label") or "Collection").strip() or "Collection"
        safe_name = base[:28]
        n = 2
        while safe_name in used_names:
            suffix = f"_{n}"
            safe_name = f"{base[: 28 - len(suffix)]}{suffix}"
            n += 1
        used_names.add(safe_name)
        sheets.append((safe_name, coll["headers"], coll["rows"]))

    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            + "".join(
                f'<Override PartName="/xl/worksheets/sheet{i}.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                for i in range(1, len(sheets) + 1)
            )
            + "</Types>",
        )
        zf.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>",
        )
        workbook_sheets = "".join(
            f'<sheet name="{_escape_xml(name)}" sheetId="{i}" r:id="rId{i}"/>'
            for i, (name, _, _) in enumerate(sheets, start=1)
        )
        zf.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f"<sheets>{workbook_sheets}</sheets></workbook>",
        )
        rels = "".join(
            f'<Relationship Id="rId{i}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{i}.xml"/>'
            for i in range(1, len(sheets) + 1)
        )
        zf.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f"{rels}</Relationships>",
        )
        for i, (name, headers, rows) in enumerate(sheets, start=1):
            zf.writestr(f"xl/worksheets/sheet{i}.xml", _sheet_xml(name, headers, rows))

    return buf.getvalue()


def _kml_coord(point) -> str | None:
    if not isinstance(point, (list, tuple)) or len(point) < 2:
        return None
    try:
        lon = float(point[0])
        lat = float(point[1])
    except (TypeError, ValueError):
        return None
    alt = 0
    if len(point) > 2:
        try:
            alt = float(point[2])
        except (TypeError, ValueError):
            alt = 0
    return f"{lon},{lat},{alt}"


def _kml_coord_ring(ring, close=False) -> str:
    pts = [_kml_coord(p) for p in (ring or [])]
    pts = [p for p in pts if p]
    if close and pts and pts[0] != pts[-1]:
        pts.append(pts[0])
    return " ".join(pts)


def _kml_geometry_xml(geometry: dict) -> str:
    if not isinstance(geometry, dict):
        return ""
    gtype = (geometry.get("type") or "").strip()
    coords = geometry.get("coordinates")

    if gtype == "Point":
        coord = _kml_coord(coords)
        return f"<Point><coordinates>{coord}</coordinates></Point>" if coord else ""

    if gtype == "MultiPoint":
        parts = []
        for pt in coords or []:
            coord = _kml_coord(pt)
            if coord:
                parts.append(f"<Point><coordinates>{coord}</coordinates></Point>")
        if not parts:
            return ""
        if len(parts) == 1:
            return parts[0]
        return f"<MultiGeometry>{''.join(parts)}</MultiGeometry>"

    if gtype == "LineString":
        line = _kml_coord_ring(coords)
        return f"<LineString><coordinates>{line}</coordinates></LineString>" if line else ""

    if gtype == "MultiLineString":
        parts = []
        for line in coords or []:
            text = _kml_coord_ring(line)
            if text:
                parts.append(
                    f"<LineString><coordinates>{text}</coordinates></LineString>"
                )
        if not parts:
            return ""
        if len(parts) == 1:
            return parts[0]
        return f"<MultiGeometry>{''.join(parts)}</MultiGeometry>"

    if gtype == "Polygon":
        rings = coords or []
        if not rings:
            return ""
        outer = _kml_coord_ring(rings[0], close=True)
        if not outer:
            return ""
        inner = "".join(
            f"<innerBoundaryIs><LinearRing><coordinates>{_kml_coord_ring(ring, close=True)}"
            "</coordinates></LinearRing></innerBoundaryIs>"
            for ring in rings[1:]
            if _kml_coord_ring(ring, close=True)
        )
        return (
            "<Polygon>"
            f"<outerBoundaryIs><LinearRing><coordinates>{outer}</coordinates></LinearRing></outerBoundaryIs>"
            f"{inner}"
            "</Polygon>"
        )

    if gtype == "MultiPolygon":
        parts = []
        for poly in coords or []:
            xml = _kml_geometry_xml({"type": "Polygon", "coordinates": poly})
            if xml:
                parts.append(xml)
        if not parts:
            return ""
        if len(parts) == 1:
            return parts[0]
        return f"<MultiGeometry>{''.join(parts)}</MultiGeometry>"

    if gtype == "GeometryCollection":
        parts = [
            _kml_geometry_xml(child)
            for child in geometry.get("geometries") or []
        ]
        parts = [p for p in parts if p]
        if not parts:
            return ""
        if len(parts) == 1:
            return parts[0]
        return f"<MultiGeometry>{''.join(parts)}</MultiGeometry>"

    return ""


def build_kml_bytes(geojson: dict, document_name: str = "Export") -> bytes:
    """Convert a GeoJSON FeatureCollection to KML 2.2 for Google Earth / GIS."""
    features = geojson.get("features") if isinstance(geojson, dict) else None
    if not isinstance(features, list):
        features = []

    placemarks = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        geom_xml = _kml_geometry_xml(feature.get("geometry") or {})
        if not geom_xml:
            continue
        props = feature.get("properties") or {}
        if not isinstance(props, dict):
            props = {}
        name = (
            props.get("field_label")
            or props.get("collection_label")
            or props.get("name")
            or "Feature"
        )
        if props.get("id") is not None:
            name = f"{name} ({props['id']})"
        data_xml = "".join(
            f'<Data name="{_escape_xml(key)}"><value>{_escape_xml(value)}</value></Data>'
            for key, value in props.items()
            if value is not None and value != ""
        )
        extended = (
            f"<ExtendedData>{data_xml}</ExtendedData>" if data_xml else ""
        )
        placemarks.append(
            "<Placemark>"
            f"<name>{_escape_xml(name)}</name>"
            f"{extended}"
            f"{geom_xml}"
            "</Placemark>"
        )

    body = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<kml xmlns="http://www.opengis.net/kml/2.2">'
        "<Document>"
        f"<name>{_escape_xml(document_name)}</name>"
        f"{''.join(placemarks)}"
        "</Document>"
        "</kml>"
    )
    return body.encode("utf-8")


def build_csv_bytes(export_table: dict) -> bytes:
    import csv
    from io import StringIO

    stream = StringIO()
    writer = csv.writer(stream)
    writer.writerow([h["label"] for h in export_table["headers"]])
    for row in export_table["rows"]:
        writer.writerow(row)
    return stream.getvalue().encode("utf-8-sig")


def build_spss_labels_bytes(export_table: dict) -> bytes:
    import csv
    from io import StringIO

    stream = StringIO()
    writer = csv.writer(stream)
    writer.writerow(["variable", "label", "type"])
    for item in export_table.get("labels") or []:
        writer.writerow([item["name"], item["label"], item.get("type", "")])
    for coll in export_table.get("collections") or []:
        for h in coll.get("headers") or []:
            writer.writerow([
                f"{coll.get('label')}.{h['id']}",
                h["label"],
                "collection_field",
            ])
    return stream.getvalue().encode("utf-8-sig")


def build_json_bytes(export_table: dict) -> bytes:
    headers = export_table["headers"]
    records = []
    for row in export_table["rows"]:
        record = {}
        for h, val in zip(headers, row):
            if isinstance(val, str) and val.startswith(("{", "[")):
                try:
                    record[h["id"]] = json.loads(val)
                    continue
                except Exception:
                    pass
            record[h["id"]] = val
        records.append(record)

    payload = {
        "form": export_table.get("title"),
        "count": len(records),
        "data": records,
        "collections": [
            {
                "label": c["label"],
                "headers": c["headers"],
                "rows": c["rows"],
            }
            for c in export_table.get("collections") or []
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, default=str).encode("utf-8")


@transaction.atomic
def delete_web_row_service(form, row_id: int) -> None:
    """Delete a physical submission row and its SubmissionIndex (+ cascaded media)."""
    from apps.submissions.models import SubmissionIndex

    _ensure_live_submissions(form)
    table_name = form.submission_table_name
    if not table_name:
        raise ValueError("Form has no submission table.")

    with connection.cursor() as cursor:
        cursor.execute(
            sql.SQL("DELETE FROM {} WHERE id = %s").format(sql.Identifier(table_name)),
            [row_id],
        )
        if cursor.rowcount == 0:
            raise LookupError("Row not found.")

    SubmissionIndex.objects.filter(form=form, physical_row_id=row_id).delete()

