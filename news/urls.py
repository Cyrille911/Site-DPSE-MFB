from django.urls import path
from . import views

urlpatterns = [
    ## Actualité
    path('liste', views.news_list, name='news_list'),  # Liste des actualités
    path('detail/<int:pk>/', views.news_detail, name='news_detail'),  # Détail d'une actualité
    path('ajout/', views.add_news, name='add_news'),  # Création d'une actualité
    path('edit/<int:pk>/', views.edit_news, name='edit_news'),  # Modification d'une actualité
    path('delete/<int:pk>/', views.delete_news, name='delete_news'),
    path('commentaire/ajout/<int:pk>/', views.add_newscomment, name='add_newscomment'),
    path('commentaire/modification/<int:pk>/', views.edit_newscomment, name='edit_newscomment'),
    path('commentaire/supprimer/<int:pk>/', views.delete_newscomment, name='delete_newscomment'),
]
