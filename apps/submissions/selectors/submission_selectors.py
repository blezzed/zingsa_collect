import json
from django.db import connection
from django.contrib.gis.geos import GEOSGeometry
from psycopg2 import sql

from apps.submissions.models import SubmissionIndex

def get_submissions_by_form_selector(form) -> list[dict]:
    """
    Reads all dynamic answers stored in the physical PostGIS table.
    """
    table_name = form.submission_table_name
    if not table_name:
        return []
        
    with connection.cursor() as cursor:
        query = sql.SQL("SELECT * FROM {}").format(sql.Identifier(table_name))
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            row_dict = {}
            for col, val in zip(columns, row):
                # Format geometry values into readable GeoJSON formats
                if val is not None and any(geom_key in col.lower() for geom_key in ('geom', 'location', 'point', 'line', 'polygon', 'boundary', 'area')):
                    try:
                        geom = GEOSGeometry(val)
                        row_dict[col] = json.loads(geom.geojson)
                    except Exception:
                        row_dict[col] = str(val)
                else:
                    # Deserialize lists and dicts
                    if isinstance(val, str) and val.startswith(('{', '[')):
                        try:
                            row_dict[col] = json.loads(val)
                        except Exception:
                            row_dict[col] = val
                    else:
                        row_dict[col] = val
            results.append(row_dict)
        return results


def get_submission_details_selector(submission_id: str) -> dict:
    """
    Retrieves metadata index and matching physical table answers.
    """
    try:
        sub_index = SubmissionIndex.objects.select_related('project', 'form', 'form_version', 'submitted_by').get(id=submission_id)
    except SubmissionIndex.DoesNotExist:
        return None
        
    table_name = sub_index.physical_table_name
    row_id = sub_index.physical_row_id
    
    with connection.cursor() as cursor:
        query = sql.SQL("SELECT * FROM {} WHERE id = %s").format(sql.Identifier(table_name))
        cursor.execute(query, [row_id])
        row = cursor.fetchone()
        
        if not row:
            return {
                'metadata': sub_index,
                'answers': {}
            }
            
        columns = [col[0] for col in cursor.description]
        answers = {}
        for col, val in zip(columns, row):
            if val is not None and any(geom_key in col.lower() for geom_key in ('geom', 'location', 'point', 'line', 'polygon', 'boundary', 'area')):
                try:
                    geom = GEOSGeometry(val)
                    answers[col] = json.loads(geom.geojson)
                except Exception:
                    answers[col] = str(val)
            else:
                if isinstance(val, str) and val.startswith(('{', '[')):
                    try:
                        answers[col] = json.loads(val)
                    except Exception:
                        answers[col] = val
                else:
                    answers[col] = val
                    
        return {
            'metadata': sub_index,
            'answers': answers
        }
