# Written by hand. makemigrations was not run.
# Depends on 0006_project_name_unique_per_owner, the latest migration in this
# worktree. Another branch adds 0007_project_invite; point this file at that
# migration when merging.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0006_project_name_unique_per_owner"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="contact_name",
            field=models.CharField(blank=True, default="", max_length=150),
        ),
        migrations.AddField(
            model_name="project",
            name="contact_phone",
            field=models.CharField(blank=True, default="", max_length=30),
        ),
        migrations.AddField(
            model_name="project",
            name="contact_email",
            field=models.EmailField(blank=True, default="", max_length=254),
        ),
        migrations.AddField(
            model_name="project",
            name="contact_note",
            field=models.CharField(blank=True, default="", max_length=300),
        ),
    ]
