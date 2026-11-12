from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from restaurants import views as restaurant_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('', restaurant_views.restaurant_list, name='home'),
    path('accounts/', include('accounts.urls')),
    path('restaurants/', include('restaurants.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)