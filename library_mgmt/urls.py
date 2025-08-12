from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

# Optional import if you use auth views here; probably not needed if all auth URLs are in app urls.py
from django.contrib.auth import views as auth_views

# If you want to reference landing_page view directly (optional)
from library.views import landing_page

urlpatterns = [
    path('admin/', admin.site.urls),

    # Main app urls
    path('', include('library.urls')),

    # Optionally redirect root URL to landing page (if not handled by library.urls)
    # path('', landing_page, name='landing_page'),

    # You generally do NOT define login/logout here if defined in library.urls
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
