from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path , include

def trigger_error(request):
    division_by_zero = 1 / 0

urlpatterns = [
    path('admin/', admin.site.urls),
    path('studio/', include('app_studio.urls')), 
    path('api-auth/', include('rest_framework.urls')),
    path('__debug__/', include('debug_toolbar.urls')),
    path('sentry-debug/', trigger_error),
]

# if settings.DEBUG:
urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
