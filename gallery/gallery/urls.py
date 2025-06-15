from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.views.generic import RedirectView

# УДАЛИТЬ ЭТУ СТРОКУ: app_name = 'main'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('gallery/', include('main.urls', namespace='main')),
    path('', RedirectView.as_view(url='game/', permanent=True)),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)