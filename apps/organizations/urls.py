from django.urls import path
from .views.organization_views import OrganizationListCreateView, OrganizationDetailView
from .views.member_views import OrganizationMemberListCreateView, OrganizationMemberDetailView

app_name = 'organizations'

urlpatterns = [
    path('', OrganizationListCreateView.as_view(), name='list_create'),
    path('<uuid:org_id>/', OrganizationDetailView.as_view(), name='detail'),
    path('<uuid:org_id>/members/', OrganizationMemberListCreateView.as_view(), name='member_list_create'),
    path('<uuid:org_id>/members/<str:username>/', OrganizationMemberDetailView.as_view(), name='member_detail'),
]

