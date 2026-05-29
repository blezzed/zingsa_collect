from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from apps.organizations.models import Organization, OrganizationMember

User = get_user_model()

class OrganizationMemberTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(username='org_admin', password='password123')
        self.target_user = User.objects.create_user(username='org_collector', password='password123')
        self.client.force_authenticate(user=self.admin_user)

        self.org = Organization.objects.create(name='Test Org')
        OrganizationMember.objects.create(organization=self.org, user=self.admin_user, role='admin')

    def test_add_valid_member(self):
        url = reverse('organizations:member_list_create', kwargs={'org_id': self.org.id})
        payload = {"username": "org_collector", "role": "member"}
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(OrganizationMember.objects.filter(user=self.target_user, role='member').exists())

    def test_add_invalid_member(self):
        url = reverse('organizations:member_list_create', kwargs={'org_id': self.org.id})
        payload = {"username": "does_not_exist", "role": "member"}
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("User with this username does not exist.", str(response.data))

    def test_update_member_role(self):
        # Add them first
        member = OrganizationMember.objects.create(organization=self.org, user=self.target_user, role='member')
        
        url = reverse('organizations:member_detail', kwargs={'org_id': self.org.id, 'username': 'org_collector'})
        payload = {"role": "admin"}
        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        member.refresh_from_db()
        self.assertEqual(member.role, 'admin')

    def test_remove_member(self):
        OrganizationMember.objects.create(organization=self.org, user=self.target_user, role='member')
        
        url = reverse('organizations:member_detail', kwargs={'org_id': self.org.id, 'username': 'org_collector'})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(OrganizationMember.objects.filter(user=self.target_user).exists())
