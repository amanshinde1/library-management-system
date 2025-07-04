"""
URL configuration for library_mgmt project.

The `urlpatterns` list routes URLs to views. For more information please fsee:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views
from library.views import landing_page

urlpatterns = [
    path('admin/', admin.site.urls),

    # ✅ Landing page at root
    path('', landing_page, name='landing'),

    # ✅ App routes (books/, borrowed/, etc.)
    path('', include('library.urls')),

    # ✅ Login page
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),

    path('library/', include(('library.urls', 'library'), namespace='library')),

    path('captcha/', include('captcha.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)