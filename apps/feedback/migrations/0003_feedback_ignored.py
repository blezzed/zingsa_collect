from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("feedback", "0002_feedback_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="feedback",
            name="status_note",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AlterField(
            model_name="feedback",
            name="status",
            field=models.CharField(
                choices=[
                    ("open", "Open"),
                    ("in_progress", "In progress"),
                    ("solved", "Solved"),
                    ("ignored", "Ignored"),
                ],
                db_index=True,
                default="open",
                max_length=32,
            ),
        ),
    ]
