#!/usr/bin/env python3
from pathlib import Path
import re
from datetime import datetime

p = Path("/home/zingsa/Documents/zingsa_collect/.env")
bak = p.with_name(f".env.bak-ip-migration-{datetime.now():%Y%m%d%H%M%S}")
bak.write_bytes(p.read_bytes())
text = p.read_text()
text = text.replace("172.30.5.24", "172.16.3.24")
text = text.replace("DJANGO_DB_HOST=172.16.3.24", "DJANGO_DB_HOST=127.0.0.1")
text = text.replace("REDIS_URL=redis://172.16.3.24:8201/0", "REDIS_URL=redis://127.0.0.1:8201/0")
text = text.replace("CELERY_BROKER_URL=redis://172.16.3.24:8201/1", "CELERY_BROKER_URL=redis://127.0.0.1:8201/1")
text = text.replace("CELERY_RESULT_BACKEND=redis://172.16.3.24:8201/2", "CELERY_RESULT_BACKEND=redis://127.0.0.1:8201/2")
text = text.replace("AWS_S3_ENDPOINT_URL=http://172.16.3.24:9018", "AWS_S3_ENDPOINT_URL=http://127.0.0.1:9018")
new_custom = "AWS_S3_CUSTOM_DOMAIN=172.16.3.24:8206/minio/zingsa-collect-media"
if "AWS_S3_CUSTOM_DOMAIN=" in text:
    text = re.sub(r"^AWS_S3_CUSTOM_DOMAIN=.*$", new_custom, text, flags=re.M)
else:
    text += "\n" + new_custom + "\n"
if "MINIO_PROXY_UPSTREAM=" not in text:
    text += "MINIO_PROXY_UPSTREAM=http://minio:9000\n"
hosts_line = next((ln for ln in text.splitlines() if ln.startswith("DJANGO_ALLOWED_HOSTS=")), "")
if "172.16.3.24" not in hosts_line:
    text = text.replace("DJANGO_ALLOWED_HOSTS=", "DJANGO_ALLOWED_HOSTS=172.16.3.24,", 1)
p.write_text(text)
print("backup:", bak.name)
print("env updated")
