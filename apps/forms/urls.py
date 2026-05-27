from django.urls import path
from apps.forms.views.form_views import (
    FormDetailView, FormPublishView, AvailableFormsView, FormDownloadView
)
from apps.submissions.views.submission_views import FormSubmissionsListView
from apps.forms.views.field_type_views import FormFieldTypeListView

app_name = 'forms'

urlpatterns = [
    path('field-types/', FormFieldTypeListView.as_view(), name='field_types'),
    path('available/', AvailableFormsView.as_view(), name='available'),
    path('<uuid:pk>/', FormDetailView.as_view(), name='detail'),
    path('<uuid:pk>/publish/', FormPublishView.as_view(), name='publish'),
    path('<uuid:pk>/download/', FormDownloadView.as_view(), name='download'),
    path('<uuid:form_id>/submissions/', FormSubmissionsListView.as_view(), name='submissions'),
]
