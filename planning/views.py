# Modules Django
from django.shortcuts import render, get_object_or_404, redirect
# Imports spécifiques au projet
from .models import PlanAction, Effet, Produit, Action, Activite

## Plan d'Actions
def plan_action_list(request):
    plans = PlanAction.objects.all()
    return render(request, 'planning/plan_action_list.html', {'plans': plans})

def plan_action_detail(request, id):
    plan = PlanAction.objects.get(id=id)
    return render(request, 'planning/plan_action_detail.html', {'plan': plan})

def add_plan_action(request):
    if request.method == 'POST':
        titre = request.POST.get('titre')
        horizon = request.POST.get('horizon')
        impact = request.POST.get('impact')

        # Validation du champ horizon
        try:
            horizon = int(horizon)
            if horizon <= 0:
                raise ValueError("L'horizon doit être un entier positif.")
        except ValueError:
            return render(request, 'planning/add_plan_action.html', {'error': "L'horizon doit être un entier positif."})

        # Création du plan d'action
        plan = PlanAction.objects.create(titre=titre, horizon=horizon, impact=impact)

        # Gestion des effets
        effet_index = 1
        while f"effet_titre_{effet_index}" in request.POST:
            effet_titre = request.POST.get(f"effet_titre_{effet_index}")
            effet = Effet.objects.create(plan=plan, titre=effet_titre)

            produit_index = 1
            while f"produit_titre_{effet_index}.{produit_index}" in request.POST:
                produit_titre = request.POST.get(f"produit_titre_{effet_index}.{produit_index}")
                produit = Produit.objects.create(effet=effet, titre=produit_titre)

                action_index = 1
                while f"action_titre_{effet_index}.{produit_index}.{action_index}" in request.POST:
                    action_titre = request.POST.get(f"action_titre_{effet_index}.{produit_index}.{action_index}")
                    action = Action.objects.create(produit=produit, titre=action_titre)

                    activite_index = 1
                    while f"activite_titre_{effet_index}.{produit_index}.{action_index}.{activite_index}" in request.POST:
                        activite_titre = request.POST.get(f"activite_titre_{effet_index}.{produit_index}.{action_index}.{activite_index}")
                        Activite.objects.create(action=action, titre=activite_titre)
                        activite_index += 1

                    action_index += 1

                produit_index += 1

            effet_index += 1

        return redirect('plan_action_list')  # Rediriger après l'ajout

    return render(request, 'planning/add_plan_action.html')

def edit_plan_action(request, id):
    plan = get_object_or_404(PlanAction, id=id)
    
    if request.method == 'POST':
        # Mise à jour des informations du plan d'action
        plan.titre = request.POST.get('titre')
        plan.horizon = request.POST.get('horizon')
        plan.impact = request.POST.get('impact')

        # Validation du champ horizon
        try:
            plan.horizon = int(plan.horizon)
            if plan.horizon <= 0:
                raise ValueError("L'horizon doit être un entier positif.")
        except ValueError:
            return render(request, 'planning/edit_plan_action.html', {'plan': plan, 'error': "L'horizon doit être un entier positif."})
        
        plan.save()

        # Suppression des anciennes relations
        plan.effets.all().delete()

        # Gestion des effets
        effet_index = 1
        while f"effet_titre_{effet_index}" in request.POST:
            effet_titre = request.POST.get(f"effet_titre_{effet_index}")
            effet = Effet.objects.create(plan=plan, titre=effet_titre)

            produit_index = 1
            while f"produit_titre_{effet_index}.{produit_index}" in request.POST:
                produit_titre = request.POST.get(f"produit_titre_{effet_index}.{produit_index}")
                produit = Produit.objects.create(effet=effet, titre=produit_titre)

                action_index = 1
                while f"action_titre_{effet_index}.{produit_index}.{action_index}" in request.POST:
                    action_titre = request.POST.get(f"action_titre_{effet_index}.{produit_index}.{action_index}")
                    action = Action.objects.create(produit=produit, titre=action_titre)

                    activite_index = 1
                    while f"activite_titre_{effet_index}.{produit_index}.{action_index}.{activite_index}" in request.POST:
                        activite_titre = request.POST.get(f"activite_titre_{effet_index}.{produit_index}.{action_index}.{activite_index}")
                        Activite.objects.create(action=action, titre=activite_titre)
                        activite_index += 1

                    action_index += 1

                produit_index += 1

            effet_index += 1

        return redirect('plan_action_list')  # Redirection après modification

    return render(request, 'planning/edit_plan_action.html', {'plan': plan})


## Liste des activiités par struture
def task_list(request):
    return render(request, 'planning/task_list.html', {})