from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from common.spa_views import serve_ux_ui

urlpatterns = [
    path('admin/', admin.site.urls),

    # API Schema and Documentation (drf-spectacular)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Authentication (Djoser + SimpleJWT)
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.jwt')),

    # Applications
    path('api/accounts/', include('apps.accounts.urls')),
    path('api/organizations/', include('apps.organizations.urls')),
    path('api/projects/', include('apps.projects.urls')),
    path('api/forms/', include('apps.forms.urls')),
    path('api/submissions/', include('apps.submissions.urls')),
    path('api/media/', include('apps.mediafiles.urls')),
    path('api/sync/', include('apps.sync.urls')),
    path('api/geospatial/', include('apps.geospatial.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    path('api/feedback/', include('apps.feedback.urls')),

    # Web-specific Data Endpoints
    path('api/web/', include('apps.submissions.web_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Next.js static export (must be last — catch-all for non-API routes)
if getattr(settings, 'UX_UI_ENABLED', False):
    urlpatterns += [
        path('', serve_ux_ui, name='ux_ui_root'),
        re_path(r'^(?P<resource>.*)$', serve_ux_ui, name='ux_ui'),
    ]
