from django.urls import path
from .views.organization_views import OrganizationListCreateView, OrganizationDetailView

app_name = 'organizations'

urlpatterns = [
    path('', OrganizationListCreateView.as_view(), name='list_create'),
    path('<uuid:org_id>/', OrganizationDetailView.as_view(), name='detail'),
]

