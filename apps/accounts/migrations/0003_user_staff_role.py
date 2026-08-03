# Generated manually for staff_role

from django.db import migrations, models


def assign_developer_to_superusers(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(is_superuser=True).update(staff_role=5, is_staff=True)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_user_profile_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="staff_role",
            field=models.PositiveSmallIntegerField(
                blank=True,
                choices=[
                    (1, "Support"),
                    (2, "Ops"),
                    (3, "Manager"),
                    (4, "Admin"),
                    (5, "Developer"),
                ],
                help_text="Platform staff grade. Null = normal Collect end-user.",
                null=True,
            ),
        ),
        migrations.RunPython(assign_developer_to_superusers, noop_reverse),
    ]
