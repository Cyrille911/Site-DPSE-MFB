from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('',include('general.urls')),
    path('admin/', admin.site.urls),
    path('user/',include('users.urls')),
    path('blog/',include('blog.urls')),
    path('documents/',include('documents.urls')),
    path('news/',include('news.urls')),
    path('planification/',include('planning.urls')),
    path('statistiques/',include('stats.urls')),
    path('qualité/',include('quality.urls')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
