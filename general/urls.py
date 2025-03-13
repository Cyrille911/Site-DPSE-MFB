from django.urls import path
from . import views

urlpatterns = [
    # Accueil
    path('', views.accueil, name='accueil'),  # Page d'accueil  ## MFB
    
    # Présentation MFB
    path('mfb-présentation/', views.mfb_presentation, name='mfb_presentation'),  # 
    path('mfb-structures/', views.mfb_structures, name='mfb_structures'),  # 
    path('discussion/', views.faq, name='faq'),
    path('glossaire/', views.glossaire, name='glossaire'),  # Glossaire
]
