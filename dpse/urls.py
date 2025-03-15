from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('',include('general.urls')),
    path('admin/', admin.site.urls),
    path('User/',include('users.urls')),
    path('Blog/',include('blog.urls')),
    path('Documents/',include('documents.urls')),
    path('News/',include('news.urls')),
    path('Planification/',include('planning.urls')),
    path('Statistiques/',include('stats.urls')),
    path('Qualité/',include('quality.urls')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
