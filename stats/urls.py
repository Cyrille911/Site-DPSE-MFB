from django.urls import path
from . import views

urlpatterns = [
    ###Statistiques du MFB
    path('', views.afficher_donnees, name='stats'),
]
