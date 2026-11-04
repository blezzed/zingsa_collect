# Written by hand. makemigrations was not run.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='submissionindex',
            name='capture_info',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='submissionindex',
            name='gps_accuracy_m',
            field=models.FloatField(blank=True, db_index=True, null=True),
        ),
    ]
