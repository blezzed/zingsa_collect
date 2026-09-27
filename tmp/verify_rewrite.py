from django.db import connection

c = connection.cursor()
c.execute(
    """
    SELECT LEFT(photos::text, 260)
    FROM collect_business_unit_survey_1_v1_f94cb5ef
    WHERE photos::text LIKE %s
    LIMIT 1
    """,
    ["%jpeg%"],
)
row = c.fetchone()
print(row[0] if row else "none")

c.execute(
    """
    SELECT COUNT(*) FROM collect_business_unit_survey_1_v1_f94cb5ef
    WHERE photos::text LIKE %s
    """,
    ["%172.30.5.24:9018%"],
)
print("old_host_remaining", c.fetchone()[0])
c.execute(
    """
    SELECT COUNT(*) FROM collect_business_unit_survey_1_v1_f94cb5ef
    WHERE photos::text LIKE %s
    """,
    ["%8206/minio/%"],
)
print("proxy_urls", c.fetchone()[0])
