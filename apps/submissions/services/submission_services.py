import uuid
import json
from django.db import transaction, connection
from django.utils import timezone
from django.contrib.gis.geos import GEOSGeometry
from rest_framework.exceptions import ValidationError
from psycopg2 import sql

from apps.submissions.models import SubmissionIndex, SubmissionMedia
from apps.forms.services.form_services import generate_column_mapping_service

def parse_geometry(val, col_type: str) -> str:
    """
    Safely converts coordinate structures (GeoJSON dict, WKT, or Lat/Lng string)
    into standard Well-Known Text (WKT).
    """
    if not val:
        return None
        
    if isinstance(val, dict):
        try:
            # If standard coordinate array is submitted instead of GeoJSON, format it
            if 'coordinates' not in val and 'type' not in val:
                # E.g. {"latitude": -17.82, "longitude": 31.03}
                if 'latitude' in val and 'longitude' in val:
                    lat, lng = float(val['latitude']), float(val['longitude'])
                    return f"POINT({lng} {lat})"
            val = json.dumps(val)
        except Exception:
            return None
            
    try:
        # Standard GeoJSON or WKT
        geom = GEOSGeometry(val)
        return geom.wkt
    except Exception:
        # Fallback for coordinate string "lat, lng" e.g., "-17.8252, 31.0335"
        if isinstance(val, str) and ',' in val:
            try:
                parts = [p.strip() for p in val.split(',')]
                if len(parts) == 2:
                    lat, lng = float(parts[0]), float(parts[1])
                    return f"POINT({lng} {lat})"
            except ValueError:
                pass
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
        
    table_name = form_version.physical_table_name
    if not table_name:
        raise ValidationError(f"Form version '{form_version.id}' does not have a physical table mapped.")
        
    column_mapping = form_version.column_mapping
    questions = form_version.schema.get('questions', [])
    
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
