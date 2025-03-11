from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),  # Dashboard TOFE
    path('douanes_dashboard/', views.douanes_dashboard, name='douanes_dashboard'),  # Dashboard Douanes
    path('get_tableau_data/', views.get_tableau_data, name='get_tableau_data'),
    path('financements_dashboard/', views.financements_dashboard, name='financements_dashboard'), # Dashboard Financements
    path('get_financements_data/', views.get_financements_data, name='get_financements_data'),
]