from django.db import migrations, models
import apps.projects.privileges


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0002_projectmember"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="role_privileges",
            field=models.JSONField(
                blank=True,
                default=apps.projects.privileges.default_role_privileges,
                help_text="Default privileges per project role (manager/collector).",
            ),
        ),
        migrations.AddField(
            model_name="projectmember",
            name="privilege_overrides",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="Per-member privilege overrides. Missing keys inherit the role defaults.",
            ),
        ),
    ]
