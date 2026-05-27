from django.urls import path
from apps.sync.views.sync_views import SingleSubmissionSyncView, BulkSubmissionSyncView, SyncStatusDetailView

app_name = 'sync'

urlpatterns = [
    path('submissions/', SingleSubmissionSyncView.as_view(), name='single_sync'),
    path('submissions/bulk/', BulkSubmissionSyncView.as_view(), name='bulk_sync'),
    path('status/<uuid:pk>/', SyncStatusDetailView.as_view(), name='status'),
]
