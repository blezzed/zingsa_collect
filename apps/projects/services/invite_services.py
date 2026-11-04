import hashlib
import hmac
import secrets
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.projects.models.invite import (
    FAILED_ATTEMPT_LIMIT,
    INVITE_DEFAULT_EXPIRY_DAYS,
    INVITE_MAX_EXPIRY_DAYS,
    INVITE_MAX_USES,
    INVITE_MIN_USES,
    ProjectInvite,
    ProjectInviteJoin,
)
from apps.projects.models.member import ProjectMember
from apps.projects.models.project import Project
from apps.projects.services.member_services import add_project_member_service

# No look-alikes: 0/O, 1/I/L.
INVITE_CODE_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
INVITE_CODE_LENGTH = 8
INVALID_INVITE_DETAIL = 'This invite or code is not valid.'

# Same length as a real sha256$salt$digest so a missing invite still hashes.
_DUMMY_CODE_HASH = 'sha256$' + ('ab' * 16) + '$' + ('cd' * 32)


def normalize_invite_code(raw: str) -> str:
    return (raw or '').strip().upper()


def make_code_hash(normalized_code: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.sha256(f'{salt}:{normalized_code}'.encode()).hexdigest()
    return f'sha256${salt}${digest}'


def code_hash_matches(stored: str, normalized_code: str) -> bool:
    """Constant-time compare. A missing or broken hash still does one digest."""
    parts = (stored or '').split('$')
    if len(parts) != 3 or parts[0] != 'sha256' or not parts[1] or not parts[2]:
        candidate = hashlib.sha256(normalized_code.encode()).hexdigest()
        return hmac.compare_digest(candidate, 'cd' * 32) and False
    candidate = hashlib.sha256(f'{parts[1]}:{normalized_code}'.encode()).hexdigest()
    if len(candidate) != len(parts[2]):
        return False
    return hmac.compare_digest(candidate, parts[2])


def _generate_invite_code() -> str:
    return ''.join(secrets.choice(INVITE_CODE_ALPHABET) for _ in range(INVITE_CODE_LENGTH))


def _resolve_expiry(expires_at):
    if expires_at is None:
        return timezone.now() + timedelta(days=INVITE_DEFAULT_EXPIRY_DAYS)
    limit = timezone.now() + timedelta(days=INVITE_MAX_EXPIRY_DAYS)
    if expires_at > limit:
        raise ValidationError({
            'expires_at': ["Expiry can't be more than 90 days from now."],
        })
    return expires_at


def _validate_max_uses(max_uses: int) -> int:
    if isinstance(max_uses, bool) or not isinstance(max_uses, int):
        raise ValidationError({'max_uses': ['max_uses must be from 1 to 1000.']})
    if max_uses < INVITE_MIN_USES or max_uses > INVITE_MAX_USES:
        raise ValidationError({'max_uses': ['max_uses must be from 1 to 1000.']})
    return max_uses


def _record_failed_attempt(invite: ProjectInvite) -> None:
    invite.failed_attempts += 1
    fields = ['failed_attempts', 'updated_at']
    if invite.failed_attempts >= FAILED_ATTEMPT_LIMIT and invite.locked_at is None:
        invite.locked_at = timezone.now()
        fields.append('locked_at')
    invite.save(update_fields=fields)


def _lock_invite(token: str) -> ProjectInvite | None:
    return (
        ProjectInvite.objects.select_for_update(of=('self',))
        .select_related('project')
        .filter(token=token)
        .first()
    )


def _join_body(project, role: str, already_member: bool) -> dict:
    return {
        'project_id': str(project.id),
        'project_name': project.name,
        'role': role,
        'already_member': already_member,
    }


def create_project_invite_service(
    *,
    project,
    created_by,
    max_uses: int,
    expires_at,
    label: str = '',
) -> tuple[ProjectInvite, str]:
    """Create an invite. Returns the row and the plain code, once."""
    max_uses = _validate_max_uses(max_uses)
    expires_at = _resolve_expiry(expires_at)
    label = (label or '').strip()
    if len(label) > 200:
        raise ValidationError({'label': ['Label must be 200 characters or fewer.']})

    plain_code = _generate_invite_code()
    code_hash = make_code_hash(plain_code)

    for _ in range(5):
        try:
            with transaction.atomic():
                invite = ProjectInvite.objects.create(
                    project=project,
                    created_by=created_by,
                    label=label,
                    token=secrets.token_urlsafe(32),
                    code_hash=code_hash,
                    expires_at=expires_at,
                    max_uses=max_uses,
                )
            return invite, plain_code
        except IntegrityError:
            continue
    raise ValidationError({'detail': 'Could not create an invite. Try again.'})


def cancel_project_invite_service(invite: ProjectInvite) -> ProjectInvite:
    """Cancel is permanent. People who already joined stay members."""
    if invite.cancelled_at is None:
        invite.cancelled_at = timezone.now()
        invite.save(update_fields=['cancelled_at', 'updated_at'])
    return invite


@transaction.atomic
def verify_project_invite_service(*, token: str, code: str) -> dict | None:
    """Check a code without using a slot. None means the generic failure."""
    normalized = normalize_invite_code(code)
    invite = _lock_invite(token)
    if invite is None:
        code_hash_matches(_DUMMY_CODE_HASH, normalized)
        return None
    if not code_hash_matches(invite.code_hash, normalized):
        _record_failed_attempt(invite)
        return None
    if not invite.accepts_new_collector():
        return None
    return {
        'valid': True,
        'project_name': invite.project.name,
    }


@transaction.atomic
def join_project_invite_service(*, token: str, code: str, user) -> dict | None:
    """
    Add the user as a collector.
    None means the generic failure. An existing member does not use a slot.
    """
    normalized = normalize_invite_code(code)
    invite = _lock_invite(token)
    if invite is None:
        code_hash_matches(_DUMMY_CODE_HASH, normalized)
        return None
    if not code_hash_matches(invite.code_hash, normalized):
        _record_failed_attempt(invite)
        return None
    if not invite.accepts_existing_member():
        return None

    project = invite.project
    # Serialize joins on this project so two invites can't both add the same person.
    Project.objects.select_for_update().get(pk=project.id)
    member = (
        ProjectMember.objects.select_for_update()
        .filter(project_id=project.id, user=user)
        .first()
    )
    if member is not None:
        return _join_body(project, member.role, True)
    if project.owner_id == user.id:
        return _join_body(project, 'manager', True)

    already_joined = ProjectInviteJoin.objects.filter(invite=invite, user=user).exists()
    if already_joined:
        return None
    if not invite.accepts_new_collector():
        return None

    add_project_member_service(
        project=project,
        username=user.username,
        role='collector',
    )
    ProjectInviteJoin.objects.create(invite=invite, user=user)
    invite.uses += 1
    invite.save(update_fields=['uses', 'updated_at'])
    return _join_body(project, 'collector', False)
