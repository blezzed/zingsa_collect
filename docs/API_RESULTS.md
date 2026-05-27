# ZINGSA Collect — API Test Results & Reference

**Test run:** All E2E flow tests passed (`apps.forms.tests.test_collect_flow.ZingsaCollectFlowTestCase`).

**Base URL (local Docker):** `http://localhost:8206`

**Authentication:** JWT Bearer tokens (Djoser + SimpleJWT).

---

## Error responses (all Collect APIs)

Every Collect API error uses a consistent JSON envelope (configured via `EXCEPTION_HANDLER` in Django settings):

```json
{
  "success": false,
  "error": {
    "code": "not_found",
    "message": "Project not found.",
    "errors": null
  },
  "detail": "Project not found."
}
```

**Validation errors** include field-level detail:

```json
{
  "success": false,
  "error": {
    "code": "validation_error",
    "message": "Validation failed.",
    "errors": {
      "title": ["This field is required."]
    }
  },
  "detail": "Validation failed.",
  "title": ["This field is required."]
}
```

| HTTP | `error.code` | Typical cause |
|------|----------------|---------------|
| 400 | `validation_error` | Invalid payload / serializer errors |
| 400 | `business_rule_violation` | Domain rule (e.g. form not publishable) |
| 401 | `not_authenticated` | Missing or invalid JWT |
| 403 | `permission_denied` | Insufficient org/project role |
| 404 | `not_found` | Organization, project, form, submission, etc. |
| 409 | `conflict` | Duplicate key / integrity constraint |
| 503 | `database_error` | PostgreSQL failure |
| 503 | `storage_error` | MinIO / S3 unavailable |
| 500 | `internal_error` | Unexpected server error |

Djoser auth endpoints (`/api/auth/…`) use Djoser’s default error format.

---

## Test Summary

| Step | Endpoint | Result |
|------|----------|--------|
| User registration | `POST /api/auth/users/` | Pass |
| JWT login | `POST /api/auth/jwt/create/` | Pass |
| Organization create | `POST /api/organizations/` | Pass — creator assigned `admin` role |
| Project create | `POST /api/projects/` | Pass — auto `PROJ-*` code, creator is `manager` |
| Form create | `POST /api/projects/{id}/forms/` | Pass — flat JSON from `full_clean.json` |
| Form publish | `POST /api/forms/{id}/publish/` | Pass — dynamic PostGIS table created |
| Submission sync | `POST /api/sync/submissions/` | Pass — row written to physical table |

---

## 1. Authentication

### Register User

```bash
curl -X POST http://localhost:8206/api/auth/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "field_officer_01",
    "email": "officer@zingsa.test",
    "password": "SecureTestPass123!",
    "re_password": "SecureTestPass123!"
  }'
```

**Response (201):**

```json
{
  "id": 1,
  "username": "field_officer_01",
  "email": "officer@zingsa.test"
}
```

### Obtain JWT Token

```bash
curl -X POST http://localhost:8206/api/auth/jwt/create/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "field_officer_01",
    "password": "SecureTestPass123!"
  }'
```

**Response (200):**

```json
{
  "refresh": "<refresh_token>",
  "access": "<access_token>"
}
```

Use the access token on all subsequent requests:

```bash
-H "Authorization: Bearer <access_token>"
```

### Refresh Token

```bash
curl -X POST http://localhost:8206/api/auth/jwt/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<refresh_token>"}'
```

---

## 2. Organization

### Create Organization

```bash
curl -X POST http://localhost:8206/api/organizations/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Mapping Org",
    "code": "ORG-TEST-001"
  }'
```

**Response (201):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Test Mapping Org",
  "code": "ORG-TEST-001",
  "created_at": "2026-05-27T20:00:00Z",
  "updated_at": "2026-05-27T20:00:00Z"
}
```

**Side effect:** `OrganizationMember` created with `role: admin` for the authenticated user.

### List Organizations

```bash
curl http://localhost:8206/api/organizations/ \
  -H "Authorization: Bearer <access_token>"
```

---

## 3. Project

### Create Project

```bash
curl -X POST http://localhost:8206/api/projects/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Wildlife Monitoring",
    "description": "Monitoring wild species.",
    "organization": "<org_uuid>",
    "status": "active"
  }'
```

**Response (201):**

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "name": "Wildlife Monitoring",
  "code": "PROJ-A1B2C3",
  "description": "Monitoring wild species.",
  "organization": "550e8400-e29b-41d4-a716-446655440000",
  "owner": 1,
  "status": "active",
  "created_at": "2026-05-27T20:01:00Z",
  "updated_at": "2026-05-27T20:01:00Z"
}
```

**Behavior:**
- `code` is auto-generated as `PROJ-<6-char-hex>` when omitted.
- Creator is assigned `ProjectMember` with `role: manager`.

### List Projects

```bash
curl http://localhost:8206/api/projects/ \
  -H "Authorization: Bearer <access_token>"
```

---

## 4. Forms

### Create Form (flat mobile JSON)

Send the flat schema directly (same structure as `full_clean.json` → `test_form_1`). Update `projectId` to match the project's `code`.

```bash
curl -X POST http://localhost:8206/api/projects/<project_uuid>/forms/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d @form_payload.json
```

**Minimal example (`form_payload.json`):**

```json
{
  "formId": "test_form_1",
  "title": "Community GIS Survey",
  "description": "Comprehensive GIS data collection form",
  "version": "v1.0",
  "mode": "map_first",
  "geometryType": "mixed",
  "projectId": "PROJ-A1B2C3",
  "questions": [
    {
      "id": "location_name",
      "type": "text",
      "label": "Location Name",
      "required": true
    },
    {
      "id": "propertyLine",
      "type": "line",
      "label": "Property Boundary Line",
      "required": false
    },
    {
      "id": "propertyPolygon",
      "type": "polygon",
      "label": "Property Boundary Polygon",
      "required": false
    }
  ]
}
```

**Response (201):**

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "title": "Community GIS Survey",
  "slug": "community-gis-survey",
  "description": "Comprehensive GIS data collection form",
  "mode": "map_first",
  "geometry_type": "mixed",
  "status": "draft",
  "project": "660e8400-e29b-41d4-a716-446655440001",
  "created_by": 1,
  "submission_table_name": null,
  "created_at": "2026-05-27T20:02:00Z",
  "updated_at": "2026-05-27T20:02:00Z"
}
```

**Side effect:** `FormVersion` v1 draft created with `column_mapping` derived from question IDs.

### Publish Form

```bash
curl -X POST http://localhost:8206/api/forms/<form_uuid>/publish/ \
  -H "Authorization: Bearer <access_token>"
```

**Response (200):**

```json
{
  "detail": "Form 'Community GIS Survey' successfully published to table 'collect_community_gis_survey_v1'.",
  "physical_table_name": "collect_community_gis_survey_v1",
  "version_number": 1
}
```

**Behavior:**
- Locks the draft version (`is_published: true`).
- Creates a physical PostgreSQL table (e.g. `collect_community_gis_survey_v1`) with:
  - System columns: `id`, `submission_uuid`, `project_id`, `form_id`, `form_version_id`, `device_id`, `client_submission_id`, `sync_status`, timestamps.
  - Custom columns mapped from question IDs (e.g. `propertyline` → `GEOMETRY(LineString)`, `propertypolygon` → `GEOMETRY(Polygon)`).
- GIST indexes on geometry columns.

### Download Published Form Definition

```bash
curl http://localhost:8206/api/forms/<form_uuid>/download/ \
  -H "Authorization: Bearer <access_token>"
```

---

## 5. Submission Sync

### Single Submission Sync

```bash
curl -X POST http://localhost:8206/api/sync/submissions/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-officer-alpha",
    "client_submission_id": "sub-gis-001",
    "form_version_id": "<form_version_uuid>",
    "answers": {
      "location_name": "Harare CBD Survey Point",
      "coordinates": "-17.8252, 31.0335",
      "land_use": "commercial",
      "description": "Central business district mapping node."
    }
  }'
```

**Response (201 — new submission):**

```json
{
  "is_duplicate": false,
  "submission": {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "client_submission_id": "sub-gis-001",
    "device_id": "device-officer-alpha",
    "sync_status": "synced",
    "physical_table_name": "collect_community_gis_survey_v1",
    "physical_row_id": 1
  }
}
```

**Response (200 — duplicate):**

```json
{
  "is_duplicate": true,
  "submission": { "...same id..." }
}
```

---

## Data Models

### User (`accounts.User`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | Integer | Primary key |
| `username` | String | Unique login |
| `email` | String | Optional |
| `password` | String | Hashed |

### Organization (`collect_organization`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Primary key |
| `name` | String | Display name |
| `code` | String | Unique org code |
| `created_at` | DateTime | Auto |
| `updated_at` | DateTime | Auto |

### OrganizationMember (`collect_organization_member`)

| Field | Type | Notes |
|-------|------|-------|
| `organization` | FK → Organization | |
| `user` | FK → User | |
| `role` | String | `admin` or `member` |

### Project (`collect_project`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Primary key |
| `name` | String | |
| `code` | String | Unique; auto `PROJ-*` if omitted |
| `description` | Text | Optional |
| `organization` | FK → Organization | Optional |
| `owner` | FK → User | Creator |
| `status` | String | `draft`, `active`, `archived` |

### ProjectMember (`collect_project_member`)

| Field | Type | Notes |
|-------|------|-------|
| `project` | FK → Project | |
| `user` | FK → User | |
| `role` | String | `manager`, `collector`, etc. |

### Form (`collect_form`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Primary key |
| `project` | FK → Project | |
| `title` | String | |
| `slug` | Slug | Unique per project |
| `description` | Text | Optional |
| `mode` | String | `form_first`, `map_first` |
| `geometry_type` | String | `none`, `point`, `line`, `polygon`, `mixed` |
| `status` | String | `draft`, `published`, `archived` |
| `current_version` | FK → FormVersion | Active version |
| `submission_table_name` | String | Set after publish |
| `created_by` | FK → User | |

### FormVersion (`collect_form_version`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Primary key |
| `form` | FK → Form | |
| `version_number` | Integer | |
| `version_label` | String | e.g. `1.0` |
| `schema` | JSON | Full flat mobile schema |
| `checksum` | String | SHA-256 of schema |
| `is_published` | Boolean | |
| `physical_table_name` | String | e.g. `collect_{slug}_v1` |
| `column_mapping` | JSON | `{question_id: db_column}` |
| `published_at` | DateTime | Set on publish |

### SubmissionIndex (`collect_submission_index`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Primary key |
| `project` | FK → Project | |
| `form` | FK → Form | |
| `form_version` | FK → FormVersion | |
| `submitted_by` | FK → User | Optional |
| `device_id` | String | Mobile device identifier |
| `client_submission_id` | String | Client-side unique ID |
| `physical_table_name` | String | Dynamic table name |
| `physical_row_id` | Integer | Row in dynamic table |
| `sync_status` | String | `synced`, `duplicate`, etc. |

### Dynamic Submission Table (per published form)

Created at publish time. Example: `collect_community_gis_survey_v1`

| Column | PostgreSQL Type | Source |
|--------|-----------------|--------|
| `id` | BIGSERIAL | System |
| `submission_uuid` | UUID | System |
| `project_id` | UUID | System |
| `form_id` | UUID | System |
| `form_version_id` | UUID | System |
| `submitted_by_id` | INTEGER | System |
| `device_id` | VARCHAR(255) | System |
| `client_submission_id` | VARCHAR(255) | System |
| `sync_status` | VARCHAR(50) | System |
| `synced_at` | TIMESTAMPTZ | System |
| `created_at` | TIMESTAMPTZ | System |
| `updated_at` | TIMESTAMPTZ | System |
| `{question_id}` | Mapped type | From `questions[]` |

**Question type → column type mapping:**

| Question `type` | PostgreSQL type |
|-----------------|-----------------|
| `text`, `radio`, `dropdown` | VARCHAR(255) |
| `textarea`, `image`, `voice`, `signature` | TEXT |
| `number` (integer) | INTEGER |
| `number` (decimal) | NUMERIC |
| `date` | DATE |
| `time` | TIME |
| `location`, `point` | GEOMETRY(Point, 4326) |
| `line` | GEOMETRY(LineString, 4326) |
| `polygon` | GEOMETRY(Polygon, 4326) |

---

## Running Tests

```bash
# Grant test DB permissions (service name is postgis in this project)
docker compose exec postgis psql -U postgres -c "ALTER USER zingsa_user CREATEDB;"

# Run E2E flow tests
docker compose exec web python manage.py test apps.forms.tests.test_collect_flow --verbosity=2
```

---

## Interactive API Docs

- Swagger UI: http://localhost:8206/api/docs/
- ReDoc: http://localhost:8206/api/docs/redoc/
- OpenAPI schema: http://localhost:8206/api/schema/
