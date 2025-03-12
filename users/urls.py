from django.urls import path
from . import views

urlpatterns = [
    path('inscription_membre/', views.inscription_membre, name='inscription_membre'),
    path('connexion_membre/', views.connexion_membre, name='connexion_membre'),
    path('inscription_visiteur/', views.inscription_visiteur, name='inscription_visiteur'),
    path('connexion_visiteur/', views.connexion_visiteur, name='connexion_visiteur'),
    path('activer/<uidb64>/<token>/', views.activer_compte_membre, name='activer_compte_membre'),
    path('activer_nouveau_membre/<uidb64>/<token>/', views.activer_nouveau_membre, name='activer_nouveau_membre'),
    path('activer_compte_visiteur/<uidb64>/<token>/', views.activer_compte_visiteur, name='activer_compte_visiteur'),
    path('profil/', views.profil_utilisateur, name='profil_utilisateur'),
    path('modifier_profil/', views.modifier_profil, name='modifier_profil'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('', views.accueil, name='accueil'),  # Page d'accueil par défaut
]