from django.db import migrations, models
from django.db.models.functions import Lower


def dedupe_project_names(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    seen = {}
    for project in Project.objects.order_by("created_at", "id"):
        key = (project.name or "").strip().lower()
        if not key:
            continue
        if key not in seen:
            seen[key] = 1
            continue
        seen[key] += 1
        suffix = project.code or str(project.id)[:8]
        project.name = f"{project.name} ({suffix})"
        project.save(update_fields=["name"])


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0004_viewer_role"),
    ]

    operations = [
        migrations.RunPython(dedupe_project_names, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="project",
            constraint=models.UniqueConstraint(
                Lower("name"),
                name="collect_project_name_ci_uniq",
            ),
        ),
    ]
