from django.urls import path
from apps.projects.views.project_views import (
    ProjectListCreateView,
    ProjectDetailView,
    ProjectRolePrivilegesView,
)
from apps.forms.views.form_views import ProjectFormListCreateView
from apps.projects.views.member_views import ProjectMemberListCreateView, ProjectMemberDetailView

app_name = 'projects'

urlpatterns = [
    path('', ProjectListCreateView.as_view(), name='list_create'),
    path('<uuid:pk>/', ProjectDetailView.as_view(), name='detail'),
    path('<uuid:project_id>/forms/', ProjectFormListCreateView.as_view(), name='form_list_create'),
    path(
        '<uuid:project_id>/privileges/',
        ProjectRolePrivilegesView.as_view(),
        name='role_privileges',
    ),
    path('<uuid:project_id>/members/', ProjectMemberListCreateView.as_view(), name='member_list_create'),
    path(
        '<uuid:project_id>/members/<str:username>/',
        ProjectMemberDetailView.as_view(),
        name='member_detail',
    ),
]
