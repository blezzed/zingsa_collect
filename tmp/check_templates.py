from pathlib import Path
from django.conf import settings

print("BASE_DIR", settings.BASE_DIR)
print("DIRS", settings.TEMPLATES[0]["DIRS"])
print("project templates", Path("templates/maintenance.html").exists())
print("config templates", Path("config/templates/maintenance.html").exists())
for d in settings.TEMPLATES[0]["DIRS"]:
    p = Path(d) / "maintenance.html"
    print("check", p, p.exists())
