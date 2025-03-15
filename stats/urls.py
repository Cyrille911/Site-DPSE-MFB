from django.urls import path
from . import views

urlpatterns = [
    path('TOFE', views.dashboard_TOFE, name='dashboard_TOFE'),  # Dashboard TOFE
    path('Douanes/', views.douanes_dashboard, name='douanes_dashboard'),  # Dashboard Douanes
    path('Financements/', views.financements_dashboard, name='financements_dashboard'), # Dashboard Financements
    path('get_tableau_data/', views.get_tableau_data, name='get_tableau_data'),
    path('get_financements_data/', views.get_financements_data, name='get_financements_data'),
]