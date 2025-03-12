from django.urls import path
from . import views

urlpatterns = [
    ## Documents
    path('<str:document_type>/', views.document_list, name='document_list'),
    path('<str:document_type>/<int:pk>/', views.document_detail, name='document_detail'),
    path('<str:document_type>/ajout/', views.add_document, name='add_document'),  # Détail d'un document
    path('<str:document_type>/modif/<int:pk>/', views.edit_document, name='edit_document'),
    path('<str:document_type>/delete/<int:pk>/', views.delete_document, name='delete_document'),
]
