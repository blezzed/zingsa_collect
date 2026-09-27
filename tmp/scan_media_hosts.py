from django.db import connection
import re

c = connection.cursor()
c.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY 1")
tables = [r[0] for r in c.fetchall()]
print("TABLES", len(tables))
for t in tables:
    print(t)

# Find any text containing :9018 or 172.30 across all user tables
needles = ["172.30.5.24", ":9018", "minio", ".jpeg", "http://"]
for table in tables:
    if table.startswith(("django_", "auth_", "celery", "spatial_")):
        continue
    c.execute(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name=%s
        """,
        [table],
    )
    cols = [(n, t) for n, t in c.fetchall() if t in ("text", "character varying", "jsonb", "json")]
    if not cols:
        continue
    for col, _ in cols:
        try:
            c.execute(
                f'SELECT COUNT(*) FROM "{table}" WHERE "{col}"::text LIKE %s OR "{col}"::text LIKE %s OR "{col}"::text LIKE %s',
                ["%172.30.5.24%", "%:9018%", "%.jpeg%"],
            )
            n = c.fetchone()[0]
        except Exception as e:
            print("err", table, col, e)
            connection.rollback()
            continue
        if n:
            print(f"HIT {table}.{col} count={n}")
            c.execute(
                f'SELECT LEFT("{col}"::text, 400) FROM "{table}" WHERE "{col}"::text LIKE %s OR "{col}"::text LIKE %s OR "{col}"::text LIKE %s LIMIT 2',
                ["%172.30.5.24%", "%:9018%", "%http%jpeg%"],
            )
            for (sample,) in c.fetchall():
                print(" ", sample.replace("\n", " ")[:400])
