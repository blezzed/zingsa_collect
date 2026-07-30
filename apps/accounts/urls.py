from django.urls import path

from apps.accounts.views.user_views import UserSuggestView

app_name = "accounts"

urlpatterns = [
    path("users/", UserSuggestView.as_view(), name="user_suggest"),
]
