import uuid

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


FAILED_ATTEMPT_LIMIT = 20
INVITE_DEFAULT_EXPIRY_DAYS = 7
INVITE_MAX_EXPIRY_DAYS = 90
INVITE_MIN_USES = 1
INVITE_MAX_USES = 1000

# Cancelled wins, then the lock, then time, then capacity.
INVITE_STATUS_CANCELLED = 'cancelled'
INVITE_STATUS_LOCKED = 'locked'
INVITE_STATUS_EXPIRED = 'expired'
INVITE_STATUS_FULL = 'full'
INVITE_STATUS_ACTIVE = 'active'


class ProjectInvite(models.Model):
    """One shareable collector invite. The plain code is never stored."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='invites',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_project_invites',
    )
    label = models.CharField(max_length=200, blank=True, default='')
    token = models.CharField(max_length=128, unique=True, editable=False)
    code_hash = models.CharField(max_length=128, editable=False)
    expires_at = models.DateTimeField()
    max_uses = models.PositiveIntegerField()
    uses = models.PositiveIntegerField(default=0)
    failed_attempts = models.PositiveIntegerField(default=0)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'collect_project_invite'
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=Q(max_uses__gte=INVITE_MIN_USES, max_uses__lte=INVITE_MAX_USES),
                name='collect_invite_max_uses_range',
            ),
            models.CheckConstraint(
                check=Q(uses__lte=F('max_uses')),
                name='collect_invite_uses_lte_max',
            ),
        ]
        indexes = [
            models.Index(fields=['project', 'created_at'], name='collect_invite_project_created'),
        ]

    def __str__(self):
        return f'Invite {self.id} for project {self.project_id}'

    @property
    def share_url(self) -> str:
        base = (getattr(settings, 'FRONTEND_URL', '') or '').rstrip('/')
        return f'{base}/join?invite={self.token}'

    def derived_status(self, now=None) -> str:
        current = now or timezone.now()
        if self.cancelled_at is not None:
            return INVITE_STATUS_CANCELLED
        if self.locked_at is not None or self.failed_attempts >= FAILED_ATTEMPT_LIMIT:
            return INVITE_STATUS_LOCKED
        if self.expires_at <= current:
            return INVITE_STATUS_EXPIRED
        if self.uses >= self.max_uses:
            return INVITE_STATUS_FULL
        return INVITE_STATUS_ACTIVE

    def accepts_new_collector(self, now=None) -> bool:
        return self.derived_status(now) == INVITE_STATUS_ACTIVE

    def accepts_existing_member(self, now=None) -> bool:
        """A person who is already on the project does not need a free slot."""
        return self.derived_status(now) in (INVITE_STATUS_ACTIVE, INVITE_STATUS_FULL)


class ProjectInviteJoin(models.Model):
    """One row per person who joined through an invite. Kept after removal."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invite = models.ForeignKey(
        ProjectInvite,
        on_delete=models.CASCADE,
        related_name='joins',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='project_invite_joins',
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'collect_project_invite_join'
        ordering = ['joined_at']
        constraints = [
            models.UniqueConstraint(
                fields=['invite', 'user'],
                name='collect_invite_join_user_uniq',
            ),
        ]

    def __str__(self):
        return f'{self.user_id} joined invite {self.invite_id}'
