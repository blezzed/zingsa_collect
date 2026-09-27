import os
import re

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.conf import settings
from django.db import connection
from apps.mediafiles.models import MediaFile

print("CUSTOM", getattr(settings, "AWS_S3_CUSTOM_DOMAIN", None))
print("ENDPOINT", getattr(settings, "AWS_S3_ENDPOINT_URL", None))
print("USE_S3", settings.USE_S3)

print("\n=== MediaFile samples ===")
for m in MediaFile.objects.all()[:8]:
    try:
        url = m.file.url if m.file else None
    except Exception as e:
        url = f"<err {e}>"
    print(m.id, getattr(m, "original_name", None), "->", url)

# Scan submission tables for absolute media URLs still on old IP / :9018
print("\n=== scanning submission payloads for media hosts ===")
patterns = (
    r"172\.30\.5\.24",
    r":9018/",
    r"172\.16\.3\.24:9018",
    r"172\.16\.3\.24:8206/minio",
)
counts = {p: 0 for p in patterns}
samples = {p: [] for p in patterns}

with connection.cursor() as cur:
    cur.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name LIKE 'form_%'
        ORDER BY table_name
        """
    )
    tables = [r[0] for r in cur.fetchall()]

for table in tables:
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            """,
            [table],
        )
        cols = cur.fetchall()
    textish = [
        c
        for c, t in cols
        if t in ("text", "character varying", "jsonb", "json")
    ]
    if not textish:
        continue
    # Cast all candidate cols to text and search
    expr = " || ' ' || ".join([f"COALESCE({c}::text,'')" for c in textish])
    sql = f"SELECT LEFT(({expr}), 500) FROM {table} LIMIT 50"
    try:
        with connection.cursor() as cur:
            cur.execute(sql)
            rows = [r[0] for r in cur.fetchall() if r and r[0]]
    except Exception as e:
        print("skip", table, e)
        continue
    for blob in rows:
        for p in patterns:
            if re.search(p, blob):
                counts[p] += 1
                if len(samples[p]) < 3:
                    # extract a short URL-ish snippet
                    m = re.search(r"https?://[^\s\"']+" + p.replace("\\", "") if False else r"https?://[^\s\"']+", blob)
                    # simpler: find substring around pattern
                    idx = re.search(p, blob).start()
                    samples[p].append(blob[max(0, idx - 40) : idx + 120])

for p, n in counts.items():
    print(f"{p}: {n}")
    for s in samples[p]:
        print("  sample:", s.replace("\n", " ")[:180])
