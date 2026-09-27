from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from common.maintenance_views import maintenance_bypass, maintenance_bypass_clear
from common.minio_proxy import minio_proxy
from common.spa_views import serve_ux_ui

urlpatterns = [
    path('__owner/maintenance-bypass/', maintenance_bypass, name='maintenance-bypass'),
    path(
        '__owner/maintenance-bypass/clear/',
        maintenance_bypass_clear,
        name='maintenance-bypass-clear',
    ),
    path('admin/', admin.site.urls),

    # Same-origin MinIO proxy (media via :8206 when :9018 is firewalled).
    re_path(r'^minio/(?P<path>.*)$', minio_proxy, name='minio-proxy'),

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
    path('api/releases/', include('apps.releases.urls')),

    # Web-specific Data Endpoints
    path('api/web/', include('apps.submissions.web_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Next.js static export (must be last — catch-all for non-API routes).
# Never match api/ or admin/: unmatched API paths (and slashless ones like
# /api/forms/available) must fall through so APPEND_SLASH / DRF 404 work.
# Otherwise the SPA returns index.html and mobile JSON clients break.
if getattr(settings, 'UX_UI_ENABLED', False):
    urlpatterns += [
        path('', serve_ux_ui, name='ux_ui_root'),
        re_path(
            r'^(?!api(?:/|$)|admin(?:/|$)|minio(?:/|$)|__owner(?:/|$))(?P<resource>.*)$',
            serve_ux_ui,
            name='ux_ui',
        ),

    ]
