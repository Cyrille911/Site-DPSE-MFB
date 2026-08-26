from django.urls import path
from . import views

urlpatterns = [
    ## Blog
    path('liste', views.blog_list, name='blog_list'),  # Liste des articles
    path('detail/<int:pk>/', views.blog_detail, name='blog_detail'),  # Détail d'un article
    path('ajout/', views.add_blog, name='add_blog'),  # Création d'un article
    path('edit/<int:pk>/', views.edit_blog, name='edit_blog'),  # Modification d'un article
    path('delete/<int:pk>/', views.delete_blog, name='delete_blog'),
    path('commentaire/ajout/', views.add_blogcomment, name='add_blogcomment'),
    path('commentaire/modification/<int:pk>/', views.edit_blogcomment, name='edit_blogcomment'),
    path('commentaire/supprimer/<int:pk>/', views.delete_blogcomment, name='delete_blogcomment'),
]
