from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from apps.projects.models import Project, ProjectMember
from apps.organizations.models import Organization

User = get_user_model()

class ProjectMemberTests(APITestCase):
    def setUp(self):
        self.manager_user = User.objects.create_user(username='proj_manager', password='password123')
        self.target_user = User.objects.create_user(username='proj_collector', password='password123')
        self.client.force_authenticate(user=self.manager_user)

        self.org = Organization.objects.create(name='Test Org')
        self.project = Project.objects.create(name='Test Proj', code='TP', owner=self.manager_user, organization=self.org)
        # Owner is automatically a manager due to project signals (if implemented), but let's ensure it here:
        ProjectMember.objects.get_or_create(project=self.project, user=self.manager_user, defaults={'role': 'manager'})

    def test_add_valid_member(self):
        url = reverse('projects:member_list_create', kwargs={'project_id': self.project.id})
        payload = {"username": "proj_collector", "role": "collector"}
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ProjectMember.objects.filter(user=self.target_user, role='collector').exists())

    def test_add_invalid_member(self):
        url = reverse('projects:member_list_create', kwargs={'project_id': self.project.id})
        payload = {"username": "does_not_exist", "role": "collector"}
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("User with this username does not exist.", str(response.data))

    def test_update_member_role(self):
        member = ProjectMember.objects.create(project=self.project, user=self.target_user, role='collector')
        
        url = reverse('projects:member_detail', kwargs={'project_id': self.project.id, 'username': 'proj_collector'})
        payload = {"role": "manager"}
        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        member.refresh_from_db()
        self.assertEqual(member.role, 'manager')

    def test_remove_member(self):
        ProjectMember.objects.create(project=self.project, user=self.target_user, role='collector')
        
        url = reverse('projects:member_detail', kwargs={'project_id': self.project.id, 'username': 'proj_collector'})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ProjectMember.objects.filter(user=self.target_user).exists())
