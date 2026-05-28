import json
from django.db import connection
from django.contrib.gis.geos import GEOSGeometry
from psycopg2 import sql
from rest_framework.exceptions import ValidationError

from apps.forms.selectors.form_selectors import get_form_by_id_selector
from apps.submissions.selectors.submission_selectors import get_submission_details_selector

def get_web_geojson_service(form, user=None) -> dict:
    """
    Returns only the geometries from the physical table, optimized for map rendering.
    Output is standard FeatureCollection GeoJSON.
    """
    table_name = form.submission_table_name
    if not table_name:
        return {"type": "FeatureCollection", "features": []}

    # Identify geometry columns based on schema
    version = form.current_version
    geom_cols = []
    if version and version.column_mapping:
        questions = version.schema.get('questions', [])
        for q in questions:
            if q.get('type') in ['point', 'line', 'polygon', 'geometry']:
                if q.get('id') in version.column_mapping:
                    geom_cols.append(version.column_mapping[q['id']])
    
    # Fallback to dynamic column detection if schema is missing mapping somehow
    if not geom_cols:
        return {"type": "FeatureCollection", "features": []}
        
    features = []
    with connection.cursor() as cursor:
        cols_to_select = ['id'] + geom_cols
        col_identifiers = [sql.Identifier(c) for c in cols_to_select]
        
        query = sql.SQL("SELECT {cols} FROM {table}").format(
            cols=sql.SQL(", ").join(col_identifiers),
            table=sql.Identifier(table_name)
        )
        
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                row_id = row[0]
                # Combine all geometries for this row (usually just 1, but we handle multiple)
                # For simplicity, we just use the first non-null geometry as the primary feature geometry
                primary_geom = None
                properties = {"id": row_id}
                
                for i, geom_val in enumerate(row[1:]):
                    col_name = geom_cols[i]
                    if geom_val:
                        try:
                            geom = GEOSGeometry(geom_val)
                            geom_json = json.loads(geom.geojson)
                            if not primary_geom:
                                primary_geom = geom_json
                            properties[col_name] = geom_json
                        except Exception:
                            pass
                            
                if primary_geom:
                    features.append({
                        "type": "Feature",
                        "geometry": primary_geom,
                        "properties": properties
                    })
        except Exception:
            # Table might not exist or error in query
            pass
            
    return {
        "type": "FeatureCollection",
        "features": features
    }


def get_web_columns_service(form) -> list:
    """
    Returns column metadata for the frontend attribute table.
    """
    version = form.current_version
    if not version or not version.column_mapping:
        return []
        
    questions = version.schema.get('questions', [])
    columns = []
    
    # Standard metadata columns
    columns.extend([
        {"id": "id", "label": "ID", "type": "number"},
        {"id": "submission_uuid", "label": "Submission UUID", "type": "text"},
        {"id": "synced_at", "label": "Synced At", "type": "datetime"},
    ])
    
    for q in questions:
        col_name = version.column_mapping.get(q['id'])
        if col_name:
            columns.append({
                "id": col_name,
                "label": q.get('label', q['id']),
                "type": q.get('type', 'text')
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
    
    with connection.cursor() as cursor:
        # Get total count
        cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table_name)))
        total_rows = cursor.fetchone()[0]
        
        # Get columns, stripping geometry completely
        cursor.execute(sql.SQL("SELECT * FROM {} LIMIT 0").format(sql.Identifier(table_name)))
        all_columns = [desc[0] for desc in cursor.description]
        
        # Identify geometry columns based on schema
        version = form.current_version
        geom_cols = []
        if version and version.column_mapping:
            questions = version.schema.get('questions', [])
            for q in questions:
                if q.get('type') in ['point', 'line', 'polygon', 'geometry']:
                    if q.get('id') in version.column_mapping:
                        geom_cols.append(version.column_mapping[q['id']])
                        
        # Filter out geometry columns for the table view
        safe_columns = [col for col in all_columns if col not in geom_cols]
        
        if not safe_columns:
            safe_columns = ['id'] # Fallback
            
        col_identifiers = [sql.Identifier(c) for c in safe_columns]
        
        query = sql.SQL("SELECT {cols} FROM {table} ORDER BY id DESC LIMIT %s OFFSET %s").format(
            cols=sql.SQL(", ").join(col_identifiers),
            table=sql.Identifier(table_name)
        )
        
        cursor.execute(query, [limit, offset])
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            row_dict = {}
            for col, val in zip(safe_columns, row):
                if isinstance(val, str) and val.startswith(('{', '[')):
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
        "limit": limit
    }
