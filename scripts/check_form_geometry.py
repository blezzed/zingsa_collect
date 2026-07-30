"""One-off: check Business Unit Survey forms for geometry data."""
from django.db import connection

from apps.forms.models import Form
from apps.submissions.models import SubmissionIndex
from apps.submissions.services.web_data_services import (
    get_web_geojson_service,
    get_web_paginated_data_service,
)
from apps.forms.services.question_schema import walk_all_questions, SPATIAL_QUESTION_TYPES

forms = Form.objects.filter(title__icontains="Business Unit Survey").select_related(
    "current_version"
)
print(f"Found {forms.count()} form(s)\n")

for f in forms:
    v = f.current_version
    print("---", f.title)
    print("  id:", f.id)
    print("  geometry_type:", f.geometry_type)
    print("  mode:", f.mode)
    print("  table:", f.submission_table_name)
    print("  published:", v.is_published if v else None)

    spatial_qids = []
    geom_cols = []
    if v and v.schema:
        for q in walk_all_questions(v.schema.get("questions", [])):
            if q.get("type") in SPATIAL_QUESTION_TYPES:
                spatial_qids.append((q.get("id"), q.get("type")))
        for qid, _ in spatial_qids:
            col = (v.column_mapping or {}).get(qid)
            if col:
                geom_cols.append(col)
    print("  spatial_questions:", spatial_qids)
    print("  geometry_columns:", geom_cols)

    index_count = SubmissionIndex.objects.filter(form=f).count()
    data = get_web_paginated_data_service(f, 1, 5)
    gj = get_web_geojson_service(f)
    print("  submission_index:", index_count)
    print("  physical_rows:", data["total"])
    print("  geojson_features:", len(gj.get("features", [])))

    if f.submission_table_name and geom_cols and data["total"] > 0:
        col = geom_cols[0]
        with connection.cursor() as cursor:
            cursor.execute(
                f'SELECT id, "{col}" IS NOT NULL AS has_geom FROM "{f.submission_table_name}" LIMIT 10'
            )
            rows = cursor.fetchall()
            with_geom = sum(1 for _, has in rows if has)
            print(f"  rows_with_{col}:", with_geom, "of sample", len(rows))
            cursor.execute(
                f'SELECT id, ST_AsText("{col}") FROM "{f.submission_table_name}" WHERE "{col}" IS NOT NULL LIMIT 2'
            )
            for row in cursor.fetchall():
                print("  sample_geom:", row)
    print()
