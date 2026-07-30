import json
from django.db import connection, transaction
from django.contrib.gis.geos import GEOSGeometry
from psycopg2 import sql

from apps.forms.services.question_schema import (
    SPATIAL_QUESTION_TYPES,
    collection_question_columns,
    nested_questions,
    walk_all_questions,
    walk_storage_questions,
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


def _coerce_to_geojson(value):
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
            try:
                geom = GEOSGeometry(stripped)
                return json.loads(geom.geojson)
            except Exception:
                return None

    if isinstance(value, (list, tuple)) and len(value) == 2:
        try:
            # Prefer [lng, lat] GeoJSON order; also accept if clearly lat/lng ZA range
            a, b = float(value[0]), float(value[1])
            return {"type": "Point", "coordinates": [a, b]}
        except (TypeError, ValueError):
            return None

    if isinstance(value, dict):
        if _is_geojson_geometry(value):
            return {
                "type": value["type"],
                "coordinates": value["coordinates"],
            }
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
            geom = _coerce_to_geojson(answers.get(q_id))
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
        # Fall through to deep scan if schema keys did not match stored payload shape

    if not isinstance(repeat_items, list):
        return features

    def deep_scan(node, props, path=""):
        if isinstance(node, list):
            for idx, child in enumerate(node):
                deep_scan(child, {**props, "repeat_index": props.get("repeat_index", idx)}, f"{path}[{idx}]")
            return
        if not isinstance(node, dict):
            return
        geom = _coerce_to_geojson(node)
        if geom and props.get("_from_field"):
            item_props = {
                k: v for k, v in props.items() if not k.startswith("_")
            }
            item_props.setdefault("field", props.get("_from_field"))
            item_props.setdefault("field_label", props.get("_from_field"))
            item_props["feature_key"] = _feature_key(item_props)
            features.append((geom, item_props))
            return
        for key, val in node.items():
            coerced = _coerce_to_geojson(val)
            if coerced:
                item_props = {
                    **{k: v for k, v in props.items() if not k.startswith("_")},
                    "collection_field": key,
                    "field": key,
                    "field_label": props.get("field_label") or key,
                    "source": "collection",
                }
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


def get_web_geojson_service(form, user=None) -> dict:
    """
    Returns geometries from the physical table for map rendering.
    Includes:
    - top-level geometry columns (including those under groups/sections)
    - GeoJSON / lat-lng values nested inside collection (JSONB) repeats,
      including spatial fields nested under groups within a collection item
    """
    table_name = form.submission_table_name
    if not table_name:
        return {"type": "FeatureCollection", "features": []}

    version = form.current_version
    geom_cols = []
    geom_col_ids = []
    geom_col_labels = []
    geom_col_types = []
    geom_col_groups = []  # (group_id, group_label) or (None, None)
    if version and version.column_mapping:
        questions = version.schema.get("questions", []) if version.schema else []

        def walk_spatial_columns(nodes, group_id=None, group_label=None):
            for q in nodes or []:
                if not isinstance(q, dict):
                    continue
                q_type = (q.get("type") or "").lower()
                q_id = q.get("id")
                nested = nested_questions(q)
                label = q.get("label") or q_id
                if q_type == "collection":
                    continue
                if q_type in ("section", "group", "note") and nested:
                    next_group = (group_id, group_label)
                    if q_type == "group" and q_id:
                        next_group = (q_id, label)
                    walk_spatial_columns(nested, next_group[0], next_group[1])
                    continue
                if q_type not in SPATIAL_QUESTION_TYPES or not q_id:
                    continue
                if q_id not in version.column_mapping:
                    continue
                col = version.column_mapping[q_id]
                if col in geom_cols:
                    continue
                geom_cols.append(col)
                geom_col_ids.append(q_id)
                geom_col_labels.append(label)
                geom_col_types.append(q_type)
                geom_col_groups.append((group_id, group_label))

        walk_spatial_columns(questions)

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
                    group_id, group_label = geom_col_groups[i]
                    props = {
                        **base_props,
                        "field": geom_col_ids[i],
                        "field_label": geom_col_labels[i],
                        "question_type": geom_col_types[i],
                        "source": "submission",
                    }
                    if group_id:
                        props["group"] = group_id
                        props["group_label"] = group_label
                    props["feature_key"] = _feature_key(props)
                    features.append({
                        "type": "Feature",
                        "geometry": geom_json,
                        "properties": props,
                    })
                except Exception:
                    pass

            collection_start = 1 + len(geom_cols)
            for j, (collection_q, col_name) in enumerate(collection_cols):
                raw = row[collection_start + j]
                payload = _parse_stored_json(raw)
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
    table_name = form.submission_table_name
    if not table_name:
        return {"data": [], "total": 0, "page": page, "limit": limit}

    offset = (page - 1) * limit
    version = form.current_version
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
            results.append(row_dict)

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
    table_name = form.submission_table_name
    version = form.current_version
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

