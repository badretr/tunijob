from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static


def trigger_error(request):
    1 / 0

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    # Redirect legacy /catalog/ requests to jobs list
    path('catalog/', RedirectView.as_view(pattern_name='jobs:job_list', permanent=False), name='catalog_redirect'),
	path('sentry-debug/', trigger_error, name='sentry_debug'),

    path('', include('apps.jobs.urls')),  # Keep only this one for jobs URLs
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)