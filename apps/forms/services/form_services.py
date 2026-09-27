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
from apps.forms.services.question_schema import (
    infer_geometry_type_from_questions,
    schema_has_spatial_questions,
    validate_questions_recursive,
    walk_storage_questions,
)


SYSTEM_SUBMISSION_COLUMNS = (
    "id",
    "submission_uuid",
    "project_id",
    "form_id",
    "form_version_id",
    "submitted_by_id",
    "device_id",
    "client_submission_id",
    "sync_status",
    "synced_at",
    "created_at",
    "updated_at",
)


def get_latest_published_version(form: Form):
    """Return the highest published FormVersion for collector/mobile clients."""
    return (
        form.versions.filter(is_published=True)
        .order_by("-version_number")
        .first()
    )


def apply_schema_version_label(schema: dict, version_number: int) -> dict:
    """Keep JSON schema.version in sync with FormVersion.version_number."""
    next_schema = dict(schema)
    next_schema["version"] = f"{version_number}.0"
    return next_schema


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
    validate_questions_recursive(questions)


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
    elif q_type == 'datetime':
        return 'TIMESTAMPTZ'
    elif q_type in ('radio', 'dropdown', 'select', 'barcode', 'qr', 'password'):
        return 'VARCHAR(255)'
    elif q_type in ('checkbox', 'image', 'video', 'voice', 'audio', 'signature', 'file'):
        return 'TEXT'
    elif q_type == 'contact':
        return 'JSONB'
    elif q_type == 'collection':
        return 'JSONB'
    elif q_type == 'calculated':
        return 'NUMERIC'
    elif q_type in ('rating', 'slider'):
        if q_type == 'slider' and isinstance(q.get('step'), float):
            return 'NUMERIC'
        return 'INTEGER'
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
    
    for q in walk_storage_questions(questions):
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


def physical_table_exists(table_name: str) -> bool:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = %s
            )
            """,
            [table_name],
        )
        row = cursor.fetchone()
        return bool(row and row[0])


def list_physical_table_columns(table_name: str) -> list[str]:
    if not table_name or not physical_table_exists(table_name):
        return []
    with connection.cursor() as cursor:
        cursor.execute(
            sql.SQL("SELECT * FROM {} LIMIT 0").format(sql.Identifier(table_name))
        )
        return [col[0] for col in cursor.description]


def get_live_submission_version(form: Form, fallback=None):
    """
    Physical table collectors and the web submissions grid read/write.

    After a new version is published, ``current_version`` may be an unpublished
    draft with no table. Submissions still belong on the latest published tip.
    """
    live = get_latest_published_version(form)
    if live and live.physical_table_name and physical_table_exists(live.physical_table_name):
        return live
    if form.submission_table_name and physical_table_exists(form.submission_table_name):
        match = form.versions.filter(
            physical_table_name=form.submission_table_name
        ).first()
        if match:
            return match
    if fallback and getattr(fallback, "physical_table_name", None):
        return fallback
    return None


def ensure_physical_columns_service(form_version) -> list[str]:
    """
    ADD COLUMN for any mapped question columns missing from the physical table.
    Deleted fields are left in place (soft-retire) to avoid dropping collected data.
    """
    table_name = form_version.physical_table_name
    if not table_name or not physical_table_exists(table_name):
        return []

    questions = form_version.schema.get("questions", [])
    mapping, db_types = generate_column_mapping_service(questions)
    added = []

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            """,
            [table_name],
        )
        existing = {row[0] for row in cursor.fetchall()}

        for _q_id, col_name in mapping.items():
            if col_name in existing:
                continue
            col_type = db_types.get(col_name, "TEXT")
            cursor.execute(
                sql.SQL("ALTER TABLE {} ADD COLUMN {} {}").format(
                    sql.Identifier(table_name),
                    sql.Identifier(col_name),
                    sql.SQL(col_type),
                )
            )
            added.append(col_name)
            if "GEOMETRY" in col_type.upper():
                idx_name = f"gist_{table_name}_{col_name}"
                cursor.execute(
                    sql.SQL(
                        "CREATE INDEX IF NOT EXISTS {} ON {} USING GIST ({})"
                    ).format(
                        sql.Identifier(idx_name),
                        sql.Identifier(table_name),
                        sql.Identifier(col_name),
                    )
                )

    return added


def migrate_submissions_between_tables(
    old_table: str,
    new_table: str,
    old_mapping: dict,
    new_mapping: dict,
) -> int:
    """
    Copy rows from a previous published table into the new version table.
    Shared question columns (by physical column name) are preserved.
    """
    if not old_table or not new_table or old_table == new_table:
        return 0
    if not physical_table_exists(old_table) or not physical_table_exists(new_table):
        return 0

    old_cols = set((old_mapping or {}).values())
    new_cols = set((new_mapping or {}).values())
    shared_question_cols = sorted(old_cols & new_cols)
    copy_cols = list(SYSTEM_SUBMISSION_COLUMNS[1:]) + shared_question_cols
    # Skip SERIAL id — let new table assign ids; keep submission_uuid uniqueness

    with connection.cursor() as cursor:
        cursor.execute(
            sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(new_table))
        )
        if cursor.fetchone()[0]:
            # Don't duplicate if target already has rows
            return 0

        insert_cols = sql.SQL(", ").join(sql.Identifier(c) for c in copy_cols)
        select_cols = sql.SQL(", ").join(sql.Identifier(c) for c in copy_cols)
        cursor.execute(
            sql.SQL(
                "INSERT INTO {new_table} ({cols}) SELECT {cols_select} FROM {old_table}"
            ).format(
                new_table=sql.Identifier(new_table),
                old_table=sql.Identifier(old_table),
                cols=insert_cols,
                cols_select=select_cols,
            )
        )
        return cursor.rowcount or 0


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
    has_spatial = schema_has_spatial_questions(questions)
    if not has_spatial and geometry_type != 'none':
        # Mobile supports `location` for point capture; do not seed legacy `point`.
        q_type = (
            'location'
            if geometry_type in ('mixed', 'point')
            else geometry_type
        )
        questions.append({
            'id': 'geom',
            'type': q_type,
            'label': 'Location' if q_type == 'location' else 'Geometry Feature',
            'required': False
        })
        schema['questions'] = questions
        has_spatial = True

    # Keep Form.geometry_type aligned with spatial questions in the schema
    inferred = infer_geometry_type_from_questions(schema.get('questions', []))
    if geometry_type == 'none' and inferred != 'none':
        geometry_type = inferred
    elif geometry_type == 'none' and has_spatial:
        geometry_type = inferred if inferred != 'none' else 'point'
    form.geometry_type = geometry_type
    schema['geometryType'] = geometry_type
        
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
    Publishes the current draft: bumps version when needed, creates/syncs the
    physical submission table (add columns + migrate prior rows), and marks the
    form live for collectors.
    """
    draft_version = form.current_version
    if not draft_version:
        raise ValidationError("Form does not have a version to publish.")

    previous_published = get_latest_published_version(form)

    # Re-publishing an already-published tip without a draft: fork a new version.
    if draft_version.is_published:
        max_num = (
            form.versions.all().aggregate(models.Max("version_number"))[
                "version_number__max"
            ]
            or 1
        )
        new_num = max_num + 1
        new_schema = apply_schema_version_label(draft_version.schema, new_num)
        checksum = calculate_form_checksum_service(new_schema)
        mapping, _ = generate_column_mapping_service(new_schema.get("questions", []))

        draft_version = FormVersion.objects.create(
            form=form,
            version_number=new_num,
            version_label=f"{new_num}.0",
            schema=new_schema,
            checksum=checksum,
            is_published=False,
            column_mapping=mapping,
            created_by=created_by,
        )
    else:
        # Ensure draft schema.version matches version_number before going live.
        synced = apply_schema_version_label(
            draft_version.schema, draft_version.version_number
        )
        if synced.get("version") != (draft_version.schema or {}).get("version"):
            draft_version.schema = synced
            draft_version.checksum = calculate_form_checksum_service(synced)
            draft_version.version_label = f"{draft_version.version_number}.0"
            draft_version.save(
                update_fields=["schema", "checksum", "version_label"]
            )

    table_name = generate_form_table_name_service(
        form.slug, draft_version.version_number, form.id
    )

    draft_version.physical_table_name = table_name
    draft_version.is_published = True
    draft_version.published_at = timezone.now()
    draft_version.save()

    # Collectors must only ever see one live tip — retire prior published versions.
    form.versions.filter(is_published=True).exclude(pk=draft_version.pk).update(
        is_published=False
    )

    create_physical_form_table_service(draft_version)
    # If the table already existed (IF NOT EXISTS), still add any new columns.
    ensure_physical_columns_service(draft_version)

    if (
        previous_published
        and previous_published.physical_table_name
        and previous_published.physical_table_name != table_name
    ):
        migrate_submissions_between_tables(
            previous_published.physical_table_name,
            table_name,
            previous_published.column_mapping or {},
            draft_version.column_mapping or {},
        )

    form.status = "published"
    form.current_version = draft_version
    form.submission_table_name = table_name
    form.save()

    return draft_version


@transaction.atomic
def delete_form_service(form: Form) -> None:
    """
    Deletes a form, its versions/submissions, and drops physical PostGIS tables.
    """
    table_names = {
        name
        for name in [
            form.submission_table_name,
            *[
                version.physical_table_name
                for version in form.versions.all()
            ],
        ]
        if name
    }

    with connection.cursor() as cursor:
        for table_name in table_names:
            cursor.execute(
                sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(
                    sql.Identifier(table_name)
                )
            )

    form.delete()


@transaction.atomic
def update_form_service(form: Form, data: dict, schema: dict = None, user = None) -> Form:
    """
    Updates Form configurations and handles version schema generation.

    Title and description can be changed on a published form; that writes them
    onto the working schema and forks a draft version when the tip is live.
    """
    data = dict(data or {})
    if "title" in data:
        title = (data.get("title") or "").strip()
        if not title:
            raise ValidationError("Enter a form title.")
        data["title"] = title
    if "description" in data and data["description"] is None:
        data["description"] = ""

    if schema is None and any(key in data for key in ("title", "description")):
        current = form.current_version
        if current and isinstance(current.schema, dict):
            schema = dict(current.schema)

    if schema is not None:
        schema = dict(schema)
        if "title" in data:
            schema["title"] = data["title"]
        elif schema.get("title"):
            data["title"] = str(schema["title"]).strip()
        if "description" in data:
            schema["description"] = data.get("description") or ""
        elif "description" in schema:
            data["description"] = schema.get("description") or ""

    for k, v in data.items():
        setattr(form, k, v)
    form.save()

    if schema:
        validate_form_schema_service(schema)
        
        questions = list(schema.get('questions', []))
        has_spatial = schema_has_spatial_questions(questions)
        if not has_spatial and form.geometry_type != 'none':
            q_type = (
                'location'
                if form.geometry_type in ('mixed', 'point')
                else form.geometry_type
            )
            questions.append({
                'id': 'geom',
                'type': q_type,
                'label': 'Location' if q_type == 'location' else 'Geometry Feature',
                'required': False
            })
            schema['questions'] = questions

        inferred = infer_geometry_type_from_questions(schema.get('questions', []))
        form.geometry_type = inferred
        schema['geometryType'] = inferred
        form.save()
            
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
            schema = apply_schema_version_label(schema, new_num)
            checksum = calculate_form_checksum_service(schema)
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


COLLECTOR_PROJECT_ROLES = ("manager", "collector")


def user_can_collect_form(user, form) -> bool:
    """
    Whether a user may list/download a form for field collection.
    Owners, managers, and collectors only (not viewers). Superusers allowed.
    Demo forms remain publicly available.
    """
    from apps.projects.models import ProjectMember

    if form.is_demo:
        return True

    if user is None or not getattr(user, "is_authenticated", False):
        return False

    if getattr(user, "is_superuser", False):
        return True

    project = form.project
    if project.owner_id == user.id:
        return True

    return ProjectMember.objects.filter(
        project=project,
        user=user,
        role__in=COLLECTOR_PROJECT_ROLES,
    ).exists()


def get_available_forms_service(
    project_code: str = None,
    is_demo_only: bool = False,
    user=None,
):
    """
    Returns published forms on active projects that have a live published version tip.
    Authenticated collectors only see forms for projects they own or collect on.
    """
    from django.db.models import Q

    queryset = (
        Form.objects.filter(
            status='published',
            versions__is_published=True,
            project__status='active',
        )
        .select_related('current_version', 'project')
        .prefetch_related('versions')
        .distinct()
    )
    if is_demo_only or user is None or not getattr(user, "is_authenticated", False):
        queryset = queryset.filter(is_demo=True)
    elif not getattr(user, "is_superuser", False):
        queryset = queryset.filter(
            Q(project__owner=user)
            | Q(
                project__members__user=user,
                project__members__role__in=COLLECTOR_PROJECT_ROLES,
            )
        ).distinct()
    if project_code:
        queryset = queryset.filter(project__code=project_code)
    return queryset


def download_form_definition_service(
    form_id: str,
    is_demo_only: bool = False,
    user=None,
) -> dict:
    """
    Downloads the latest published version configuration for collectors.
    """
    try:
        try:
            uuid.UUID(form_id)
            form = Form.objects.select_related('project').get(id=form_id)
        except ValueError:
            form = Form.objects.select_related('project').get(slug=form_id)
    except Form.DoesNotExist:
        raise ValidationError(f"Form with identifier '{form_id}' does not exist.")

    if is_demo_only and not form.is_demo:
        raise ValidationError(f"Form '{form.title}' is not a demo form. Authentication required.")

    if not user_can_collect_form(user, form):
        raise ValidationError(
            f"You do not have access to download form '{form.title}'."
        )

    if form.project.status != 'active':
        raise ValidationError(
            f"Form '{form.title}' belongs to a {form.project.status} project "
            "and is not available for download."
        )

    if form.status != 'published':
        raise ValidationError(f"Form '{form.title}' is not published yet.")

    version = get_latest_published_version(form)
    if not version:
        raise ValidationError(f"Form '{form.title}' has no published version yet.")
        
    schema = dict(version.schema)
    
    schema['formId'] = str(form.id)
    schema['title'] = form.title
    schema['slug'] = form.slug
    schema['mode'] = form.mode
    schema['geometryType'] = form.geometry_type
    schema['version'] = version.version_label or f"{version.version_number}.0"
    schema['version_id'] = str(version.id)
    schema['version_number'] = version.version_number
    schema['version_label'] = version.version_label
    schema['checksum'] = version.checksum
    schema['column_mapping'] = version.column_mapping
    schema['physical_table_name'] = version.physical_table_name
    schema['published_at'] = version.published_at.isoformat() if version.published_at else None
    # Mobile clients should replace any older local copy with this tip.
    schema['force_update'] = True
    schema['is_latest'] = True
    
    return schema
