import json
import re
from django.db import connection

with connection.cursor() as cur:
    cur.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema='public' AND table_name LIKE 'form_%'
        """
    )
    tables = [r[0] for r in cur.fetchall()]
print("tables", tables)

for table in tables:
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema='public' AND table_name=%s
            ORDER BY ordinal_position
            """,
            [table],
        )
        cols = cur.fetchall()
    print("\nCOLUMNS", table)
    for c, t in cols:
        print(" ", c, t)

    # dump first few rows as JSON-ish text snippets containing jpeg/png/http
    textish = [c for c, t in cols if t in ("text", "character varying", "jsonb", "json")]
    if not textish:
        continue
    select_cols = ", ".join([f'"{c}"::text AS "{c}"' for c in textish[:40]])
    sql = f'SELECT id, {select_cols} FROM "{table}" ORDER BY id DESC LIMIT 3'
    with connection.cursor() as cur:
        try:
            cur.execute(sql)
        except Exception:
            # maybe no id
            sql = f'SELECT {select_cols} FROM "{table}" LIMIT 3'
            cur.execute(sql)
        rows = cur.fetchall()
        names = [d[0] for d in cur.description]
    for row in rows:
        data = dict(zip(names, row))
        print("\nROW keys", list(data.keys())[:20])
        blob = json.dumps(data, default=str)
        for m in re.finditer(r"https?://[^\\\"'\\s]+|uploads/[^\\\"'\\s]+|\\.jpe?g|\\.png|photo|image|media", blob, re.I):
            pass
        # print interesting columns
        for k, v in data.items():
            if v is None:
                continue
            s = str(v)
            if any(x in s.lower() for x in ("http", "upload", ".jpg", ".jpeg", ".png", "photo", "minio", "172.")):
                print(f"  {k}: {s[:500]}")
