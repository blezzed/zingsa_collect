import re
import json
import hashlib
import uuid
from django.db import models, transaction, connection
from django.utils import timezone
from django.utils.text import slugify
from rest_framework.exceptions import ValidationError
from psycopg2 import sql

from apps.forms.models import Form, FormVersion

def validate_form_schema_service(schema: dict):
    """
    Validates form version schema format.
    """
    if not isinstance(schema, dict):
        raise ValidationError("Schema must be a JSON object.")
        
    required_keys = ['formId', 'title', 'version', 'mode', 'projectId', 'questions']
    for k in required_keys:
        if k not in schema:
            raise ValidationError(f"Schema is missing required field: '{k}'.")
        # Ensure strings are not empty
        val = schema[k]
        if isinstance(val, str) and not val.strip():
            raise ValidationError(f"Schema field '{k}' cannot be empty.")
            
    questions = schema.get('questions')
    if not isinstance(questions, list):
        raise ValidationError("Schema 'questions' field must be a JSON array.")
        
    if len(questions) == 0:
        raise ValidationError("Schema 'questions' array cannot be empty.")
        
    for idx, q in enumerate(questions):
        if not isinstance(q, dict):
            raise ValidationError(f"Question at index {idx} must be a JSON object.")
            
        for qk in ['id', 'type', 'label']:
            if qk not in q:
                raise ValidationError(f"Question at index {idx} is missing required field '{qk}'.")
            val = q[qk]
            if isinstance(val, str) and not val.strip():
                raise ValidationError(f"Question at index {idx} field '{qk}' cannot be empty.")


def calculate_form_checksum_service(schema: dict) -> str:
    """
    Returns a stable SHA-256 hash of the schema content.
    """
    schema_str = json.dumps(schema, sort_keys=True)
    return hashlib.sha256(schema_str.encode('utf-8')).hexdigest()


def generate_form_table_name_service(form_slug: str, version_number: int, form_id: str = None) -> str:
    """
    Returns safe snake_case table name like collect_{slug}_v{version}_{hash}.
    """
    slug = form_slug.lower().strip()
    slug = re.sub(r'[^a-z0-9_]', '_', slug)
    slug = re.sub(r'_+', '_', slug).strip('_')
    
    base_name = f"collect_{slug}_v{version_number}"
    
    if form_id:
        form_hash = str(form_id).replace("-", "")[:8].lower()
        return f"{base_name}_{form_hash}"
    return base_name


def map_question_type_to_pg(q: dict) -> str:
    """
    Maps standard question type to PostgreSQL/PostGIS types.
    """
    q_type = q.get('type')
    numeric_type = q.get('numericType')
    
    if q_type == 'text':
        return 'VARCHAR(255)'
    elif q_type == 'textarea':
        return 'TEXT'
    elif q_type == 'email':
        return 'VARCHAR(254)'
    elif q_type == 'phone':
        return 'VARCHAR(50)'
    elif q_type == 'url':
        return 'TEXT'
    elif q_type == 'number':
        if numeric_type == 'integer':
            return 'INTEGER'
        elif numeric_type in ('decimal', 'float'):
            return 'NUMERIC'
        else:
            if 'decimalPlaces' in q or 'min' in q and isinstance(q['min'], float):
                return 'NUMERIC'
            return 'INTEGER'
    elif q_type == 'date':
        return 'DATE'
    elif q_type == 'time':
        return 'TIME'
    elif q_type in ('radio', 'dropdown', 'barcode', 'qr'):
        return 'VARCHAR(255)'
    elif q_type in ('checkbox', 'image', 'video', 'voice', 'audio', 'signature', 'file'):
        return 'TEXT'
    elif q_type in ('location', 'point'):
        return 'GEOMETRY(Point, 4326)'
    elif q_type == 'line':
        return 'GEOMETRY(LineString, 4326)'
    elif q_type == 'polygon':
        return 'GEOMETRY(Polygon, 4326)'
    else:
        return 'TEXT'


def sanitize_column_name(question_id: str) -> str:
    """
    Sanitizes question IDs into safe snake_case database column names.
    """
    name = question_id.lower().strip()
    name = re.sub(r'[^a-z0-9_]', '_', name)
    name = re.sub(r'^_+', '', name)
    name = re.sub(r'_+', '_', name)
    if not name:
        name = "column"
    if name[0].isdigit():
        name = f"col_{name}"
    return name[:50].strip('_')


def generate_column_mapping_service(questions: list) -> tuple[dict, dict]:
    """
    Returns unique, safe snake_case column names and maps their types.
    """
    system_columns = {
        'id', 'submission_uuid', 'project_id', 'form_id', 'form_version_id',
        'submitted_by_id', 'device_id', 'client_submission_id', 'sync_status',
        'synced_at', 'created_at', 'updated_at'
    }
    
    mapping = {}
    db_types = {}
    used_names = set()
    
    for q in questions:
        q_id = q.get('id')
        if not q_id:
            continue
            
        base_name = sanitize_column_name(q_id)
        if base_name in system_columns:
            base_name = f"{base_name}_field"
            
        col_name = base_name
        suffix = 2
        while col_name in used_names:
            col_name = f"{base_name}_{suffix}"
            suffix += 1
            
        used_names.add(col_name)
        mapping[q_id] = col_name
        db_types[col_name] = map_question_type_to_pg(q)
        
    return mapping, db_types


def create_physical_form_table_service(form_version) -> str:
    """
    Safely creates the PostGIS physical form table and matching indexes.
    """
    table_name = form_version.physical_table_name
    column_mapping = form_version.column_mapping
    questions = form_version.schema.get('questions', [])
    
    _, db_types = generate_column_mapping_service(questions)
    
    with connection.cursor() as cursor:
        col_sqls = []
        for q_id, col_name in column_mapping.items():
            col_type = db_types.get(col_name, 'TEXT')
            col_sqls.append(
                sql.SQL("{} {}").format(
                    sql.Identifier(col_name),
                    sql.SQL(col_type)
                )
            )
            
        create_table_query = sql.SQL("""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id BIGSERIAL PRIMARY KEY,
                submission_uuid UUID NOT NULL,
                project_id UUID NOT NULL,
                form_id UUID NOT NULL,
                form_version_id UUID NOT NULL,
                submitted_by_id INTEGER,
                device_id VARCHAR(255) NOT NULL,
                client_submission_id VARCHAR(255) NOT NULL,
                sync_status VARCHAR(50) NOT NULL,
                synced_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                {custom_columns}
            )
        """).format(
            table_name=sql.Identifier(table_name),
            custom_columns=sql.SQL(", ").join(col_sqls) if col_sqls else sql.SQL(" ")
        )
        
        cursor.execute(create_table_query)
        
        indexes = [
            ("project_id", "project_id"),
            ("form_id", "form_id"),
            ("form_version_id", "form_version_id"),
            ("submitted_by_id", "submitted_by_id"),
            ("client_submission_id", "client_submission_id"),
            ("synced_at", "synced_at"),
        ]
        
        for idx_name_part, col_name in indexes:
            idx_name = f"idx_{table_name}_{idx_name_part}"
            idx_query = sql.SQL("CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name} ({col_name})").format(
                idx_name=sql.Identifier(idx_name),
                table_name=sql.Identifier(table_name),
                col_name=sql.Identifier(col_name)
            )
            cursor.execute(idx_query)
            
        for col_name, col_type in db_types.items():
            if "GEOMETRY" in col_type.upper():
                idx_name = f"gist_{table_name}_{col_name}"
                idx_query = sql.SQL("CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name} USING GIST ({col_name})").format(
                    idx_name=sql.Identifier(idx_name),
                    table_name=sql.Identifier(table_name),
                    col_name=sql.Identifier(col_name)
                )
                cursor.execute(idx_query)
                
    return table_name


@transaction.atomic
def create_form_service(
    project,
    title: str,
    created_by,
    schema: dict = None,
    mode: str = 'form_first',
    geometry_type: str = 'none',
    description: str = None
) -> Form:
    """
    Creates Form and FormVersion v1 draft inside a transaction.
    """
    slug = slugify(title)
    base_slug = slug
    counter = 1
    while Form.objects.filter(project=project, slug=slug).exists():
        slug = f"{base_slug}_{counter}"
        counter += 1
        
    form = Form.objects.create(
        project=project,
        title=title,
        slug=slug,
        description=description,
        mode=mode,
        geometry_type=geometry_type,
        status='draft',
        created_by=created_by
    )
    
    if schema is None:
        schema = {
            'formId': form.slug,
            'title': form.title,
            'description': form.description or '',
            'version': '1.0',
            'projectId': project.code,
            'questions': []
        }
    else:
        validate_form_schema_service(schema)
        
    # Inject virtual geom question for map-first forms
    questions = list(schema.get('questions', []))
    has_spatial = any(q.get('type') in ('location', 'point', 'line', 'polygon') for q in questions)
    if not has_spatial and geometry_type != 'none':
        q_type = 'location' if geometry_type == 'mixed' else geometry_type
        questions.append({
            'id': 'geom',
            'type': q_type,
            'label': 'Geometry Feature',
            'required': False
        })
        schema['questions'] = questions
        
    checksum = calculate_form_checksum_service(schema)
    mapping, _ = generate_column_mapping_service(schema.get('questions', []))
    
    version = FormVersion.objects.create(
        form=form,
        version_number=1,
        version_label="1.0",
        schema=schema,
        checksum=checksum,
        is_published=False,
        column_mapping=mapping,
        created_by=created_by
    )
    
    form.current_version = version
    form.save()
    return form


@transaction.atomic
def publish_form_service(form: Form, created_by) -> FormVersion:
    """
    Locks form draft, registers published version and spawns physical database table.
    """
    draft_version = form.current_version
    
    if draft_version.is_published:
        max_num = form.versions.all().aggregate(models.Max('version_number'))['version_number__max'] or 1
        new_num = max_num + 1
        new_schema = dict(draft_version.schema)
        new_schema['version'] = f"{new_num}.0"
        
        checksum = calculate_form_checksum_service(new_schema)
        mapping, _ = generate_column_mapping_service(new_schema.get('questions', []))
        
        draft_version = FormVersion.objects.create(
            form=form,
            version_number=new_num,
            version_label=f"{new_num}.0",
            schema=new_schema,
            checksum=checksum,
            is_published=False,
            column_mapping=mapping,
            created_by=created_by
        )
        
    table_name = generate_form_table_name_service(form.slug, draft_version.version_number, form.id)
    
    draft_version.physical_table_name = table_name
    draft_version.is_published = True
    draft_version.published_at = timezone.now()
    draft_version.save()
    
    create_physical_form_table_service(draft_version)
    
    form.status = 'published'
    form.current_version = draft_version
    form.submission_table_name = table_name
    form.save()
    
    return draft_version


@transaction.atomic
def update_form_service(form: Form, data: dict, schema: dict = None, user = None) -> Form:
    """
    Updates Form configurations and handles version schema generation.
    """
    for k, v in data.items():
        setattr(form, k, v)
    form.save()

    if schema:
        validate_form_schema_service(schema)
        
        questions = list(schema.get('questions', []))
        has_spatial = any(q.get('type') in ('location', 'point', 'line', 'polygon') for q in questions)
        if not has_spatial and form.geometry_type != 'none':
            q_type = 'location' if form.geometry_type == 'mixed' else form.geometry_type
            questions.append({
                'id': 'geom',
                'type': q_type,
                'label': 'Geometry Feature',
                'required': False
            })
            schema['questions'] = questions
            
        checksum = calculate_form_checksum_service(schema)
        mapping, _ = generate_column_mapping_service(schema.get('questions', []))
        
        current = form.current_version
        if current and not current.is_published:
            current.schema = schema
            current.checksum = checksum
            current.column_mapping = mapping
            current.save()
        else:
            max_num = form.versions.all().aggregate(models.Max('version_number'))['version_number__max'] or 1
            new_num = max_num + 1
            new_version = FormVersion.objects.create(
                form=form,
                version_number=new_num,
                version_label=f"{new_num}.0",
                schema=schema,
                checksum=checksum,
                is_published=False,
                column_mapping=mapping,
                created_by=user
            )
            form.current_version = new_version
            form.save()
    return form


def get_available_forms_service(project_code: str = None):
    """
    Returns published active forms.
    """
    queryset = Form.objects.filter(status='published').select_related('current_version')
    if project_code:
        queryset = queryset.filter(project__code=project_code)
    return queryset


def download_form_definition_service(form_id: str) -> dict:
    """
    Downloads active published version configuration.
    """
    try:
        try:
            uuid.UUID(form_id)
            form = Form.objects.get(id=form_id)
        except ValueError:
            form = Form.objects.get(slug=form_id)
    except Form.DoesNotExist:
        raise ValidationError(f"Form with identifier '{form_id}' does not exist.")
        
    if not form.current_version or form.status != 'published':
        raise ValidationError(f"Form '{form.title}' is not published yet.")
        
    version = form.current_version
    schema = dict(version.schema)
    
    schema['formId'] = str(form.id)
    schema['title'] = form.title
    schema['slug'] = form.slug
    schema['mode'] = form.mode
    schema['geometryType'] = form.geometry_type
    schema['version_id'] = str(version.id)
    schema['version_number'] = version.version_number
    schema['version_label'] = version.version_label
    schema['column_mapping'] = version.column_mapping
    schema['physical_table_name'] = version.physical_table_name
    schema['published_at'] = version.published_at.isoformat() if version.published_at else None
    
    return schema
