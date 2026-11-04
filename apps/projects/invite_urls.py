from django.urls import path

from apps.projects.views.invite_views import InviteJoinView, InviteVerifyView

app_name = 'project_invites'

urlpatterns = [
    path('<str:token>/verify/', InviteVerifyView.as_view(), name='verify'),
    path('<str:token>/join/', InviteJoinView.as_view(), name='join'),
]
