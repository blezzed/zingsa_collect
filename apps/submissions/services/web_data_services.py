import json
from django.db import connection
from django.contrib.gis.geos import GEOSGeometry
from psycopg2 import sql

from apps.forms.services.question_schema import (
    SPATIAL_QUESTION_TYPES,
    collection_question_columns,
    walk_all_questions,
    walk_storage_questions,
)


def _is_geojson_geometry(value) -> bool:
    return isinstance(value, dict) and value.get("type") and value.get("coordinates")


def _geometries_from_repeat_payload(repeat_items, base_props):
    """Extract GeoJSON geometries from a collection repeat array."""
    features = []
    if not isinstance(repeat_items, list):
        return features
    for repeat_index, item in enumerate(repeat_items):
        if not isinstance(item, dict):
            continue
        for field_id, field_val in item.items():
            if _is_geojson_geometry(field_val):
                props = {
                    **base_props,
                    "repeat_index": repeat_index,
                    "collection_field": field_id,
                }
                features.append((field_val, props))
            elif isinstance(field_val, str):
                try:
                    parsed = json.loads(field_val)
                    if _is_geojson_geometry(parsed):
                        props = {
                            **base_props,
                            "repeat_index": repeat_index,
                            "collection_field": field_id,
                        }
                        features.append((parsed, props))
                except (json.JSONDecodeError, TypeError):
                    pass
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


def get_web_geojson_service(form, user=None) -> dict:
    """
    Returns geometries from the physical table for map rendering.
    Includes top-level geometry columns and GeoJSON inside collection (JSONB) repeats.
    """
    table_name = form.submission_table_name
    if not table_name:
        return {"type": "FeatureCollection", "features": []}

    version = form.current_version
    geom_cols = []
    geom_col_ids = []
    if version and version.column_mapping:
        for q in walk_all_questions(version.schema.get("questions", [])):
            q_type = q.get("type")
            q_id = q.get("id")
            if q_type in SPATIAL_QUESTION_TYPES and q_id in version.column_mapping:
                col = version.column_mapping[q_id]
                if col not in geom_cols:
                    geom_cols.append(col)
                    geom_col_ids.append(q_id)

    collection_cols = collection_question_columns(version)

    if not geom_cols and not collection_cols:
        return {"type": "FeatureCollection", "features": []}

    features = []
    select_cols = ["id"] + geom_cols + [col for _, col in collection_cols]
    col_identifiers = [sql.Identifier(c) for c in select_cols]

    with connection.cursor() as cursor:
        query = sql.SQL("SELECT {cols} FROM {table}").format(
            cols=sql.SQL(", ").join(col_identifiers),
            table=sql.Identifier(table_name),
        )
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
        except Exception:
            return {"type": "FeatureCollection", "features": []}

        for row in rows:
            row_id = row[0]
            base_props = {"id": row_id}

            for i, geom_val in enumerate(row[1:1 + len(geom_cols)]):
                if not geom_val:
                    continue
                try:
                    geom = GEOSGeometry(geom_val)
                    geom_json = json.loads(geom.geojson)
                    features.append({
                        "type": "Feature",
                        "geometry": geom_json,
                        "properties": {
                            **base_props,
                            "field": geom_col_ids[i],
                        },
                    })
                except Exception:
                    pass

            collection_start = 1 + len(geom_cols)
            for j, (collection_id, col_name) in enumerate(collection_cols):
                raw = row[collection_start + j]
                payload = _parse_stored_json(raw)
                if payload is None:
                    continue
                for geom_json, props in _geometries_from_repeat_payload(
                    payload,
                    {**base_props, "collection": collection_id},
                ):
                    features.append({
                        "type": "Feature",
                        "geometry": geom_json,
                        "properties": props,
                    })

    return {"type": "FeatureCollection", "features": features}


def get_web_columns_service(form) -> list:
    """
    Returns column metadata for the frontend attribute table.
    """
    version = form.current_version
    if not version or not version.column_mapping:
        return []

    columns = [
        {"id": "id", "label": "ID", "type": "number"},
        {"id": "submission_uuid", "label": "Submission UUID", "type": "text"},
        {"id": "synced_at", "label": "Synced At", "type": "datetime"},
    ]

    for q in walk_storage_questions(version.schema.get("questions", [])):
        col_name = version.column_mapping.get(q["id"])
        if col_name:
            columns.append({
                "id": col_name,
                "label": q.get("label", q["id"]),
                "type": q.get("type", "text"),
            })

    return columns


def get_web_paginated_data_service(form, page: int, limit: int, user=None) -> dict:
    """
    Returns paginated tabular data, EXCLUDING heavy geometry strings
    so the grid loads extremely fast.
    """
    table_name = form.submission_table_name
    if not table_name:
        return {"data": [], "total": 0, "page": page, "limit": limit}

    offset = (page - 1) * limit
    version = form.current_version

    with connection.cursor() as cursor:
        cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table_name)))
        total_rows = cursor.fetchone()[0]

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

        col_identifiers = [sql.Identifier(c) for c in safe_columns]

        query = sql.SQL("SELECT {cols} FROM {table} ORDER BY id DESC LIMIT %s OFFSET %s").format(
            cols=sql.SQL(", ").join(col_identifiers),
            table=sql.Identifier(table_name),
        )

        cursor.execute(query, [limit, offset])
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
            results.append(row_dict)

    return {
        "data": results,
        "total": total_rows,
        "page": page,
        "limit": limit,
    }
