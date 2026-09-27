#!/usr/bin/env python3
from pathlib import Path
import re

p = Path("/home/zingsa/Documents/zingsa_collect/.env")
text = p.read_text()

# ALLOWED_HOSTS
text = re.sub(
    r"^DJANGO_ALLOWED_HOSTS=.*$",
    "DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,172.16.3.24,41.174.184.62",
    text,
    flags=re.M,
)
if "41.174.184.62" not in text.split("DJANGO_ALLOWED_HOSTS=", 1)[-1].split("\n", 1)[0]:
    text = text.replace(
        "DJANGO_ALLOWED_HOSTS=",
        "DJANGO_ALLOWED_HOSTS=41.174.184.62,",
        1,
    )

csrf = "DJANGO_CSRF_TRUSTED_ORIGINS=http://172.16.3.24:8206,http://41.174.184.62:8206,http://localhost:8206,http://127.0.0.1:8206"
if "DJANGO_CSRF_TRUSTED_ORIGINS=" in text:
    text = re.sub(r"^DJANGO_CSRF_TRUSTED_ORIGINS=.*$", csrf, text, flags=re.M)
else:
    text += "\n" + csrf + "\n"

if "PUBLIC_MEDIA_RELATIVE=" in text:
    text = re.sub(r"^PUBLIC_MEDIA_RELATIVE=.*$", "PUBLIC_MEDIA_RELATIVE=True", text, flags=re.M)
else:
    text += "PUBLIC_MEDIA_RELATIVE=True\n"

p.write_text(text)
print("updated .env hosts")
