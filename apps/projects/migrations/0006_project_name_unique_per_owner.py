from django.db import migrations, models
from django.db.models.functions import Lower


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0005_project_name_ci_unique"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="project",
            name="collect_project_name_ci_uniq",
        ),
        migrations.AddConstraint(
            model_name="project",
            constraint=models.UniqueConstraint(
                Lower("name"),
                "owner",
                name="collect_project_name_owner_ci_uniq",
            ),
        ),
    ]
