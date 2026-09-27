from django.db import connection

c = connection.cursor()
c.execute(
    """
    SELECT id, LEFT(photos::text, 700)
    FROM collect_business_unit_survey_1_v1_f94cb5ef
    WHERE photos IS NOT NULL
    ORDER BY id DESC
    LIMIT 3
    """
)
for row_id, blob in c.fetchall():
    print("ROW", row_id)
    print(blob)
    print("has_file", "file://" in (blob or ""))
    print("has_minio", "/minio/" in (blob or ""))
    print("has_http", "http://" in (blob or ""))
    print("---")
