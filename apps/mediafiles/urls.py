from django.urls import path
from .views.media_views import MediaUploadView

app_name = 'mediafiles'

urlpatterns = [
    path('upload/', MediaUploadView.as_view(), name='upload'),
]

