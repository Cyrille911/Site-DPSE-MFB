from django.urls import path
from . import views

urlpatterns = [
    path('', views.quality, name='quality'),
    path('detail/', views.quality_detail_view, name='quality_detail'),
]
