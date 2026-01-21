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
    
    # Gestion des utilisateurs (Admin Dashboard)
    path('gestion-utilisateurs/', views.manage_users, name='manage_users'),
    path('gestion-utilisateurs/toggle/<int:user_id>/', views.toggle_user_active, name='toggle_user_active'),
    path('gestion-utilisateurs/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('gestion-utilisateurs/update-role/<int:user_id>/', views.update_user_role, name='update_user_role'),
    path('gestion-utilisateurs/update-details/<int:user_id>/', views.update_user_details, name='update_user_details'),
    path('gestion-utilisateurs/update-permissions/<int:user_id>/', views.update_user_permissions, name='update_user_permissions'),

    path('déconnexion/', views.deconnexion, name='deconnexion'),
]
