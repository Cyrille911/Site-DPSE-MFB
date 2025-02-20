from django.urls import path
from . import views

urlpatterns = [  
    ## Connexion et déconnexion des Utilisateurs (Membres, Visiteurs)
    path('inscription/membre/', views.inscription_membre, name='inscription_membre'),  # 
    path('inscription/visiteur/', views.inscription_visiteur, name='inscription_visiteur'),  # 
    path('connexion/membre/', views.connexion_membre, name='connexion_membre'),  # 
    path('connexion/visiteur/', views.connexion_visiteur, name='connexion_visiteur'),  #
    path('activer/visiteur/<uidb64>/<token>/', views.activer_compte_visiteur, name='activer_compte_visiteur'), 
    path('activer/membre/<uidb64>/<token>/', views.activer_compte_membre, name='activer_compte_membre'), 
    path('nouveau/membre/<uidb64>/<token>/', views.activer_nouveau_membre, name='activer_nouveau_membre'),
    path('profil/', views.profil_utilisateur, name='profil_utilisateur'),
    path('modifier-profil/', views.modifier_profil, name='modifier_profil'),
    path('déconnexion/', views.deconnexion, name='deconnexion'),
]
