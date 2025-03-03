from django.urls import path
from . import views

urlpatterns = [
    ## Plan d'Actions
    path('liste', views.plan_action_list, name='plan_action_list'),
    path('detail/<int:id>/', views.plan_action_detail, name='plan_action_detail'),
    path('ajout/', views.add_plan_action, name='add_plan_action'),
    path('modif/<int:id>/', views.edit_plan_action, name='edit_plan_action'),
    path('gestion-activites/', views.task_list, name='task_list'),
    path('gestion-activites/save/', views.task_list, name='save_activites'),
    path('gestion-activites/delete/<int:activite_id>/', views.delete_activite, name='delete_activite'),
]
