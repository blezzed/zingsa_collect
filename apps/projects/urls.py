from django.urls import path
from apps.projects.views.project_views import ProjectListCreateView, ProjectDetailView
from apps.forms.views.form_views import ProjectFormListCreateView

app_name = 'projects'

urlpatterns = [
    path('', ProjectListCreateView.as_view(), name='list_create'),
    path('<uuid:pk>/', ProjectDetailView.as_view(), name='detail'),
    path('<uuid:project_id>/forms/', ProjectFormListCreateView.as_view(), name='form_list_create'),
]
