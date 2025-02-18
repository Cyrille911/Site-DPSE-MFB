from django.urls import path
from . import views

urlpatterns = [  
    ## Connexion et déconnexion des Utilisateurs (Membres, Visiteurs)
    path('user/inscription/membre/', views.inscription_membre, name='inscription_membre'),  # 
    path('user/inscription/visiteur/', views.inscription_visiteur, name='inscription_visiteur'),  # 
    path('user/connexion/membre/', views.connexion_membre, name='connexion_membre'),  # 
    path('user/connexion/visiteur/', views.connexion_visiteur, name='connexion_visiteur'),  #
    path('user/activer/visiteur/<uidb64>/<token>/', views.activer_compte_visiteur, name='activer_compte_visiteur'), 
    path('user/activer/membre/<uidb64>/<token>/', views.activer_compte_membre, name='activer_compte_membre'), 
    path('user/nouveau/membre/<uidb64>/<token>/', views.activer_nouveau_membre, name='activer_nouveau_membre'),
    path('user/profil/', views.profil_utilisateur, name='profil_utilisateur'),
    path('user/modifier-profil/', views.modifier_profil, name='modifier_profil'),
    path('user/déconnexion/', views.deconnexion, name='deconnexion'),
]
