from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.index, name='home.index'),
    path('about', views.about, name='home.about'),
]
urlpatterns += static(settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT)