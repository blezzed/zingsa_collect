import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0006_project_name_unique_per_owner'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectInvite',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('label', models.CharField(blank=True, default='', max_length=200)),
                ('token', models.CharField(editable=False, max_length=128, unique=True)),
                ('code_hash', models.CharField(editable=False, max_length=128)),
                ('expires_at', models.DateTimeField()),
                ('max_uses', models.PositiveIntegerField()),
                ('uses', models.PositiveIntegerField(default=0)),
                ('failed_attempts', models.PositiveIntegerField(default=0)),
                ('cancelled_at', models.DateTimeField(blank=True, null=True)),
                ('locked_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'created_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='created_project_invites',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'project',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='invites',
                        to='projects.project',
                    ),
                ),
            ],
            options={
                'db_table': 'collect_project_invite',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='projectinvite',
            constraint=models.CheckConstraint(
                check=models.Q(max_uses__gte=1, max_uses__lte=1000),
                name='collect_invite_max_uses_range',
            ),
        ),
        migrations.AddConstraint(
            model_name='projectinvite',
            constraint=models.CheckConstraint(
                check=models.Q(uses__lte=models.F('max_uses')),
                name='collect_invite_uses_lte_max',
            ),
        ),
        migrations.AddIndex(
            model_name='projectinvite',
            index=models.Index(fields=['project', 'created_at'], name='collect_invite_project_created'),
        ),
        migrations.CreateModel(
            name='ProjectInviteJoin',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                (
                    'invite',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='joins',
                        to='projects.projectinvite',
                    ),
                ),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='project_invite_joins',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'db_table': 'collect_project_invite_join',
                'ordering': ['joined_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='projectinvitejoin',
            constraint=models.UniqueConstraint(
                fields=('invite', 'user'),
                name='collect_invite_join_user_uniq',
            ),
        ),
    ]
