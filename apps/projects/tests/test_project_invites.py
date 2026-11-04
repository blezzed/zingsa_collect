from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.forms.models import Form
from apps.organizations.models import OrganizationMember
from apps.projects.models import Project, ProjectInvite, ProjectInviteJoin, ProjectMember
from apps.projects.services.invite_services import INVITE_CODE_ALPHABET
from apps.projects.views.invite_views import InviteCodeIPThrottle

User = get_user_model()

INVALID_INVITE = {'detail': 'This invite or code is not valid.'}
INVITE_FIELDS = {
    'id',
    'label',
    'status',
    'expires_at',
    'max_uses',
    'uses',
    'failed_attempts',
    'created_by',
    'created_at',
    'share_url',
    'joined',
}


def _flat_values(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _flat_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _flat_values(item)
    else:
        yield value


class ProjectInviteTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.owner = User.objects.create_user(username='invite_owner', password='password123')
        self.collector = User.objects.create_user(username='invite_collector', password='password123')
        self.joiner = User.objects.create_user(username='invite_joiner', password='password123')
        self.project = Project.objects.create(
            name='Invite Project',
            code='INVITE01',
            owner=self.owner,
        )
        ProjectMember.objects.create(project=self.project, user=self.owner, role='manager')
        ProjectMember.objects.create(project=self.project, user=self.collector, role='collector')
        self.client.force_authenticate(user=self.owner)
        self.list_url = reverse(
            'projects:invite_list_create',
            kwargs={'project_id': self.project.id},
        )

    def _create(self, **overrides):
        self.client.force_authenticate(user=self.owner)
        payload = {'max_uses': 5, 'label': 'Field team'}
        payload.update(overrides)
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        return response.data

    def _list(self):
        self.client.force_authenticate(user=self.owner)
        return self.client.get(self.list_url)

    def _token(self, created):
        row = ProjectInvite.objects.get(id=created['id'])
        return row.token

    def _verify_url(self, token):
        return reverse('project_invites:verify', kwargs={'token': token})

    def _join_url(self, token):
        return reverse('project_invites:join', kwargs={'token': token})

    def _verify(self, token, code):
        self.client.force_authenticate(user=None)
        return self.client.post(self._verify_url(token), {'code': code}, format='json')

    def _join(self, token, user, code, extra=None):
        self.client.force_authenticate(user=user)
        payload = {'code': code}
        if extra:
            payload.update(extra)
        return self.client.post(self._join_url(token), payload, format='json')

    def _assert_invalid(self, response):
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(dict(response.data), INVALID_INVITE)

    def test_owner_can_create_collector_and_anonymous_cannot(self):
        created = self._create()
        code = created['code']
        self.assertEqual(len(code), 8)
        self.assertTrue(set(code) <= set(INVITE_CODE_ALPHABET))
        self.assertTrue(set('0O1IL').isdisjoint(INVITE_CODE_ALPHABET))
        self.assertEqual(set(created.keys()), INVITE_FIELDS | {'code'})
        self.assertIn(code, list(_flat_values(created)))

        row = ProjectInvite.objects.get(id=created['id'])
        self.assertTrue(row.code_hash.startswith('sha256$'))
        self.assertNotEqual(row.code_hash, code)
        field_names = {field.name for field in ProjectInvite._meta.fields}
        self.assertNotIn('code', field_names)
        for field in ProjectInvite._meta.fields:
            value = getattr(row, field.attname)
            if isinstance(value, str):
                self.assertNotEqual(value, code)

        self.assertEqual(created['share_url'], row.share_url)
        self.assertIn(f'/join?invite={row.token}', created['share_url'])
        self.assertEqual(created['created_by'], 'invite_owner')
        self.assertEqual(created['status'], 'active')
        self.assertEqual(created['max_uses'], 5)
        self.assertEqual(created['uses'], 0)
        self.assertEqual(created['joined'], [])
        raw_expires = created['expires_at']
        expires_at = raw_expires if isinstance(raw_expires, datetime) else datetime.fromisoformat(raw_expires)
        if timezone.is_naive(expires_at):
            expires_at = timezone.make_aware(expires_at)
        remaining = expires_at - timezone.now()
        self.assertGreater(remaining, timedelta(days=6, hours=23))
        self.assertLess(remaining, timedelta(days=7, hours=1))

        listed = self._list()
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(len(listed.data), 1)
        item = listed.data[0]
        self.assertEqual(set(item.keys()), INVITE_FIELDS)
        self.assertNotIn(code, list(_flat_values(item)))
        self.assertNotIn('code_hash', item)

        self.client.force_authenticate(user=self.collector)
        refused = self.client.post(self.list_url, {'max_uses': 3}, format='json')
        self.assertEqual(refused.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=None)
        anonymous = self.client.post(self.list_url, {'max_uses': 3}, format='json')
        self.assertEqual(anonymous.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expiry_and_max_uses_are_refused_when_out_of_range(self):
        too_far = (timezone.now() + timedelta(days=91)).isoformat()
        expiry = self.client.post(
            self.list_url,
            {'max_uses': 5, 'expires_at': too_far},
            format='json',
        )
        self.assertEqual(expiry.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('expires_at', expiry.data)

        for max_uses in (0, 1001):
            response = self.client.post(
                self.list_url,
                {'max_uses': max_uses},
                format='json',
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('max_uses', response.data)

        missing = self.client.post(self.list_url, {}, format='json')
        self.assertEqual(missing.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_accepts_the_code_ignoring_case_and_spaces(self):
        created = self._create()
        token = self._token(created)
        code = created['code']

        wrong = self._verify(token, 'NOTRIGHT')
        self._assert_invalid(wrong)
        self.assertEqual(ProjectInvite.objects.get(id=created['id']).failed_attempts, 1)

        mixed = f"  {code[:4].lower()}{code[4:]}  "
        response = self._verify(token, mixed)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data.keys()), {'valid', 'project_name'})
        self.assertEqual(response.data['valid'], True)
        self.assertEqual(response.data['project_name'], 'Invite Project')
        self.assertEqual(ProjectInvite.objects.get(id=created['id']).uses, 0)
        self.assertEqual(ProjectInvite.objects.get(id=created['id']).failed_attempts, 1)

        listed = self._list()
        self.assertEqual(listed.data[0]['status'], 'active')
        self.assertEqual(listed.data[0]['failed_attempts'], 1)

    def test_every_invite_failure_returns_the_same_body(self):
        active = self._create()
        expired = self._create(label='expired')
        cancelled = self._create(label='cancelled')
        locked = self._create(label='locked')
        full = self._create(max_uses=1, label='full')
        filler = User.objects.create_user(username='invite_filler', password='password123')
        outsider = User.objects.create_user(username='invite_outsider', password='password123')

        ProjectInvite.objects.filter(id=expired['id']).update(
            expires_at=timezone.now() - timedelta(minutes=5),
        )
        cancel_url = reverse(
            'projects:invite_cancel',
            kwargs={'project_id': self.project.id, 'invite_id': cancelled['id']},
        )
        self.client.force_authenticate(user=self.owner)
        cancelled_response = self.client.post(cancel_url)
        self.assertEqual(cancelled_response.status_code, status.HTTP_200_OK)
        self.assertEqual(cancelled_response.data['status'], 'cancelled')
        self.assertNotIn('code', cancelled_response.data)

        ProjectInvite.objects.filter(id=locked['id']).update(
            failed_attempts=20,
            locked_at=timezone.now(),
        )
        filled = self._join(self._token(full), filler, full['code'])
        self.assertEqual(filled.status_code, status.HTTP_200_OK)
        self.assertEqual(filled.data['already_member'], False)

        cases = [
            (self._token(active), 'NOTRIGHT'),
            ('missing-token-value', active['code']),
            (self._token(expired), expired['code']),
            (self._token(cancelled), cancelled['code']),
            (self._token(locked), locked['code']),
            (self._token(full), full['code']),
        ]
        seen = []
        for token, code in cases:
            verify_response = self._verify(token, code)
            join_response = self._join(token, outsider, code)
            self._assert_invalid(verify_response)
            self._assert_invalid(join_response)
            seen.append(dict(verify_response.data))
            seen.append(dict(join_response.data))
        self.assertEqual(len({tuple(item.items()) for item in seen}), 1)

        listed = {item['label']: item for item in self._list().data}
        self.assertEqual(listed['Field team']['status'], 'active')
        self.assertEqual(listed['expired']['status'], 'expired')
        self.assertEqual(listed['cancelled']['status'], 'cancelled')
        self.assertEqual(listed['locked']['status'], 'locked')
        self.assertEqual(listed['full']['status'], 'full')
        self.assertEqual(listed['full']['uses'], 1)
        self.assertEqual(listed['full']['joined'][0]['username'], 'invite_filler')
        for item in listed.values():
            self.assertNotIn('code', item)
            self.assertNotIn('code_hash', item)

    def test_join_adds_a_collector_and_ignores_a_role(self):
        created = self._create(max_uses=2)
        token = self._token(created)
        response = self._join(
            token,
            self.joiner,
            created['code'],
            extra={'role': 'manager'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            dict(response.data),
            {
                'project_id': str(self.project.id),
                'project_name': 'Invite Project',
                'role': 'collector',
                'already_member': False,
            },
        )
        member = ProjectMember.objects.get(project=self.project, user=self.joiner)
        self.assertEqual(member.role, 'collector')
        invite = ProjectInvite.objects.get(id=created['id'])
        self.assertEqual(invite.uses, 1)
        self.assertEqual(ProjectInviteJoin.objects.filter(invite=invite, user=self.joiner).count(), 1)

        listed = self._list().data[0]
        self.assertEqual(set(listed['joined'][0].keys()), {'username', 'joined_at'})
        self.assertEqual(listed['joined'][0]['username'], 'invite_joiner')

    def test_max_uses_stops_the_next_person(self):
        created = self._create(max_uses=1)
        token = self._token(created)
        first = self._join(token, self.joiner, created['code'])
        self.assertEqual(first.status_code, status.HTTP_200_OK)
        other = User.objects.create_user(username='invite_next', password='password123')
        second = self._join(token, other, created['code'])
        self._assert_invalid(second)
        self.assertEqual(ProjectInvite.objects.get(id=created['id']).uses, 1)
        self.assertFalse(ProjectMember.objects.filter(project=self.project, user=other).exists())

    def test_existing_member_does_not_use_a_slot_or_change_role(self):
        created = self._create(max_uses=1)
        token = self._token(created)
        response = self._join(token, self.owner, created['code'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['already_member'], True)
        self.assertEqual(response.data['role'], 'manager')
        self.owner.refresh_from_db()
        member = ProjectMember.objects.get(project=self.project, user=self.owner)
        self.assertEqual(member.role, 'manager')
        invite = ProjectInvite.objects.get(id=created['id'])
        self.assertEqual(invite.uses, 0)
        self.assertFalse(ProjectInviteJoin.objects.filter(invite=invite, user=self.owner).exists())

        taken = self._join(token, self.joiner, created['code'])
        self.assertEqual(taken.status_code, status.HTTP_200_OK)
        self.assertEqual(ProjectInvite.objects.get(id=created['id']).uses, 1)
        again = self._join(token, self.owner, created['code'])
        self.assertEqual(again.status_code, status.HTTP_200_OK)
        self.assertEqual(again.data['already_member'], True)
        self.assertEqual(again.data['role'], 'manager')
        self.assertEqual(ProjectInvite.objects.get(id=created['id']).uses, 1)

    def test_removed_member_cannot_reuse_the_invite_but_can_use_a_new_one(self):
        created = self._create()
        token = self._token(created)
        joined = self._join(token, self.joiner, created['code'])
        self.assertEqual(joined.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.owner)
        remove_url = reverse(
            'projects:member_detail',
            kwargs={'project_id': self.project.id, 'username': self.joiner.username},
        )
        removed = self.client.delete(remove_url)
        self.assertEqual(removed.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ProjectMember.objects.filter(project=self.project, user=self.joiner).exists())
        self.assertTrue(
            ProjectInviteJoin.objects.filter(invite_id=created['id'], user=self.joiner).exists()
        )

        blocked = self._join(token, self.joiner, created['code'])
        self._assert_invalid(blocked)
        self.assertFalse(ProjectMember.objects.filter(project=self.project, user=self.joiner).exists())
        self.assertEqual(ProjectInvite.objects.get(id=created['id']).uses, 1)

        fresh = self._create(label='replacement')
        allowed = self._join(self._token(fresh), self.joiner, fresh['code'])
        self.assertEqual(allowed.status_code, status.HTTP_200_OK)
        self.assertEqual(allowed.data['already_member'], False)
        self.assertEqual(allowed.data['role'], 'collector')
        self.assertEqual(
            ProjectMember.objects.get(project=self.project, user=self.joiner).role,
            'collector',
        )
        self.assertEqual(ProjectInvite.objects.get(id=fresh['id']).uses, 1)
        self.assertEqual(ProjectInvite.objects.get(id=created['id']).uses, 1)

    def test_twenty_wrong_codes_lock_the_invite(self):
        created = self._create()
        token = self._token(created)
        for _ in range(20):
            response = self._verify(token, 'NOTRIGHT')
            self._assert_invalid(response)

        right_verify = self._verify(token, created['code'])
        self._assert_invalid(right_verify)
        right_join = self._join(token, self.joiner, created['code'])
        self._assert_invalid(right_join)

        invite = ProjectInvite.objects.get(id=created['id'])
        self.assertGreaterEqual(invite.failed_attempts, 20)
        self.assertIsNotNone(invite.locked_at)
        self.assertEqual(invite.uses, 0)
        self.assertFalse(ProjectMember.objects.filter(project=self.project, user=self.joiner).exists())
        listed = self._list().data[0]
        self.assertEqual(listed['status'], 'locked')
        self.assertEqual(listed['failed_attempts'], 20)

    def test_join_when_logged_out_is_unauthorized(self):
        created = self._create()
        self.client.force_authenticate(user=None)
        response = self.client.post(
            self._join_url(self._token(created)),
            {'code': created['code']},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(ProjectInvite.objects.get(id=created['id']).uses, 0)

    def test_cancel_keeps_people_who_already_joined(self):
        created = self._create()
        token = self._token(created)
        self._join(token, self.joiner, created['code'])
        self.client.force_authenticate(user=self.owner)
        url = reverse(
            'projects:invite_cancel',
            kwargs={'project_id': self.project.id, 'invite_id': created['id']},
        )
        first = self.client.post(url)
        second = self.client.post(url)
        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(first.data['status'], 'cancelled')
        self.assertEqual(second.data['status'], 'cancelled')
        self.assertTrue(
            ProjectMember.objects.filter(
                project=self.project,
                user=self.joiner,
                role='collector',
            ).exists()
        )
        self.assertTrue(ProjectInviteJoin.objects.filter(invite_id=created['id']).exists())
        blocked = self._join(token, User.objects.create_user(username='invite_late', password='password123'), created['code'])
        self._assert_invalid(blocked)

    def test_joined_user_without_organisation_can_open_the_project_and_forms(self):
        self.assertIsNone(self.project.organization_id)
        self.assertFalse(OrganizationMember.objects.filter(user=self.joiner).exists())
        Form.objects.create(
            project=self.project,
            title='Road count',
            slug='road-count',
            created_by=self.owner,
        )
        created = self._create()
        joined = self._join(self._token(created), self.joiner, created['code'])
        self.assertEqual(joined.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.joiner)
        project_response = self.client.get(
            reverse('projects:detail', kwargs={'pk': self.project.id})
        )
        self.assertEqual(project_response.status_code, status.HTTP_200_OK)
        self.assertEqual(project_response.data['name'], 'Invite Project')
        self.assertIn('view_forms', project_response.data['my_privileges'])

        forms_response = self.client.get(
            reverse('projects:form_list_create', kwargs={'project_id': self.project.id})
        )
        self.assertEqual(forms_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(forms_response.data), 1)
        self.assertEqual(forms_response.data[0]['title'], 'Road count')

        listed = self.client.get(reverse('projects:list_create'))
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertIn(str(self.project.id), [row['id'] for row in listed.data['results']])

    def test_verify_and_join_share_an_ip_throttle(self):
        had_rate = 'rate' in InviteCodeIPThrottle.__dict__
        previous = getattr(InviteCodeIPThrottle, 'rate', None)
        InviteCodeIPThrottle.rate = '1/min'
        try:
            created = self._create()
            token = self._token(created)
            self.client.force_authenticate(user=None)
            first = self.client.post(self._verify_url(token), {'code': 'NOTRIGHT'}, format='json')
            second = self.client.post(self._verify_url(token), {'code': 'NOTRIGHT'}, format='json')
            self.assertEqual(first.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(second.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
            self.client.force_authenticate(user=self.joiner)
            joined = self.client.post(
                self._join_url(token),
                {'code': created['code']},
                format='json',
            )
            self.assertEqual(joined.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
            self.assertFalse(
                ProjectMember.objects.filter(project=self.project, user=self.joiner).exists()
            )
        finally:
            if had_rate:
                InviteCodeIPThrottle.rate = previous
            else:
                delattr(InviteCodeIPThrottle, 'rate')
            cache.clear()
