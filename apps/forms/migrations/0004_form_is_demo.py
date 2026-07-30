# Generated manually

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('forms', '0003_formfieldtype_properties_schema'),
    ]

    operations = [
        migrations.AddField(
            model_name='form',
            name='is_demo',
            field=models.BooleanField(default=False),
        ),
    ]
