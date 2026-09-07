from django.urls import path
from . import views

urlpatterns = [
    path('pppbse-gar/', views.pppbse_gar, name='pppbse_gar'),
    path('liste/', views.plan_action_list, name='plan_action_list'),
    path('detail/<int:id>/', views.plan_action_detail, name='plan_action_detail'),
    path('ajout/', views.add_plan_action, name='add_plan_action'),
    path('modif/<int:id>/', views.edit_plan_action, name='edit_plan_action'),
    path('track_execution_list/<int:plan_id>/', views.track_execution_list, name='track_execution_list'),
    path('track_execution_detail/<int:plan_id>/', views.track_execution_detail, name='track_execution_detail'),
    path('plan/<int:plan_id>/<str:entity>/', views.manage_activities, name='manage_activities'),
    path('pao_list/<int:plan_id>/', views.pao_list, name='pao_list'),
    path('operational_plan_matrix/<int:plan_id>/<int:annee>/', views.operational_plan_matrix, name='operational_plan_matrix'),
    path('rapport_word/<int:plan_id>/<int:annee>/', views.rapport_word, name='rapport_word'),
    path('performance_matrix/<int:plan_id>/<int:annee>/', views.performance_matrix, name='performance_matrix'),
    path('hierarchy_review/<int:plan_id>/', views.hierarchy_review, name='hierarchy_review'),
    path('activite/<int:activite_id>/preuves/', views.preuves_activite, name='preuves_activite'),
    path('preuve/<int:preuve_id>/modifier/', views.modifier_preuve, name='modifier_preuve'),
    path('preuve/<int:preuve_id>/supprimer/', views.supprimer_preuve, name='supprimer_preuve'),
]