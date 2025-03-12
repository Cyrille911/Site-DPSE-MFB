from django.urls import path
from . import views

urlpatterns = [
    path('', views.quality, name='quality'),
]
