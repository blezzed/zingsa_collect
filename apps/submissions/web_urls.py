from django.urls import path
from apps.submissions.views.web_data_views import (
    WebGeoJsonView,
    WebColumnsView,
    WebDataPaginatedView,
    WebDataDetailView
)

app_name = 'web_data'

urlpatterns = [
    path('forms/<uuid:form_id>/geojson/', WebGeoJsonView.as_view(), name='geojson'),
    path('forms/<uuid:form_id>/columns/', WebColumnsView.as_view(), name='columns'),
    path('forms/<uuid:form_id>/data/', WebDataPaginatedView.as_view(), name='data_paginated'),
    path('forms/<uuid:form_id>/data/<int:row_id>/', WebDataDetailView.as_view(), name='data_detail'),
]
