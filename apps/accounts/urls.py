from django.urls import path

from apps.accounts.views.staff_views import (
    EndUserAdminDetailView,
    EndUserAdminListView,
    StaffDetailView,
    StaffListCreateView,
)
from apps.accounts.views.usage_views import AccountUsageView
from apps.accounts.views.user_views import UserSuggestView

app_name = "accounts"

urlpatterns = [
    path("users/", UserSuggestView.as_view(), name="user_suggest"),
    path("usage/", AccountUsageView.as_view(), name="account_usage"),
    path("staff/", StaffListCreateView.as_view(), name="staff_list_create"),
    path("staff/<int:user_id>/", StaffDetailView.as_view(), name="staff_detail"),
    path("users-admin/", EndUserAdminListView.as_view(), name="users_admin_list"),
    path(
        "users-admin/<int:user_id>/",
        EndUserAdminDetailView.as_view(),
        name="users_admin_detail",
    ),
]
