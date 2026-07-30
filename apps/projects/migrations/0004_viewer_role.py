from django.db import migrations, models
import apps.projects.privileges


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0003_project_privileges"),
    ]

    operations = [
        migrations.AlterField(
            model_name="projectmember",
            name="role",
            field=models.CharField(
                choices=[
                    ("manager", "Manager"),
                    ("collector", "Data Collector"),
                    ("viewer", "Viewer"),
                ],
                default="collector",
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name="project",
            name="role_privileges",
            field=models.JSONField(
                blank=True,
                default=apps.projects.privileges.default_role_privileges,
                help_text="Default privileges per project role (manager/collector/viewer).",
            ),
        ),
    ]
