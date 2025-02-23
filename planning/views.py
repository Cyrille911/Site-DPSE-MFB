# Modules Django
import json  # Pour traiter les champs JSON
from django.shortcuts import render, get_object_or_404, redirect
from .models import PlanAction, Effet, Produit, Action, Activite
from django.http import JsonResponse

## Plan d'Actions
def plan_action_list(request):
    plans = PlanAction.objects.all()
    return render(request, 'planning/plan_action_list.html', {'plans':plans})

def plan_action_detail(request, id):
    # Récupération du plan d'action
    plan = get_object_or_404(PlanAction, id=id)

    # Récupération optimisée des activités liées au plan
    activites = (
        Activite.objects
        .filter(action__produit__effet__plan=plan)
        .select_related('action__produit__effet')  # Optimisation SQL pour les relations
    )

    # Vérification si la requête est une requête AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Récupérer les filtres depuis la requête GET
        types_selectionnes = request.GET.getlist('types')  # Liste des types sélectionnés
        print(types_selectionnes)

        # Appliquer les filtres à la requête
        if types_selectionnes:
            activites = activites.filter(type__in=types_selectionnes)



        # Vérification si des activités correspondent aux critères
        if not activites.exists():
            return JsonResponse({'activites': [], 'message': 'Aucune activité trouvée'}, safe=False)

        # Sérialisation des données des activités à envoyer en réponse JSON
        data = [
            {
                'effet': getattr(activite.action.produit.effet, 'titre', "N/A"),
                'produit': getattr(activite.action.produit, 'titre', "N/A"),
                'action': getattr(activite.action, 'titre', "N/A"),
                'activite': activite.titre,
                'type': activite.type,
                'couts': activite.couts,
            }
            for activite in activites
        ]

        # Retourner les données filtrées sous forme de JSON
        return JsonResponse({'activites': data}, safe=False)

    # Si la requête n'est pas AJAX, rendre la page HTML classique
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

        # Gestion des effets, produits, actions et activités
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
                        # Récupération des informations de l'activité
                        activite_titre = request.POST.get(f"activite_titre_{effet_index}.{produit_index}.{action_index}.{activite_index}")
                        activite_type = request.POST.get(f"activite_type_{effet_index}.{produit_index}.{action_index}.{activite_index}")
                        indicateur_label = request.POST.get(f"indicateur_label_{effet_index}.{produit_index}.{action_index}.{activite_index}")
                        indicateur_reference = request.POST.get(f"indicateur_reference_{effet_index}.{produit_index}.{action_index}.{activite_index}")

                        # Récupérer la valeur de l'horizon
                        horizon = int(request.POST.get(f"horizon"))

                        # Récupérer les cibles et les coûts pour chaque période de l'horizon
                        # Initialisation des listes vides pour chaque activité
                        cibles = []
                        couts = []
                        for i in range(1, horizon + 1):
                            cible_valeur = request.POST.get(f"cible_{effet_index}.{produit_index}.{action_index}.{activite_index}[{i}]", None)
                            cout_valeur = float(request.POST.get(f"cout_{effet_index}.{produit_index}.{action_index}.{activite_index}[{i}]", None))

                            # Ajouter les valeurs aux listes cibles et couts si elles existent
                            if cible_valeur:
                                cibles.append(cible_valeur)
                            if cout_valeur:
                                couts.append(cout_valeur)

                        # Création de l'objet Activite dans la base de données avec les cibles et couts
                        point_focal = request.user

                        Activite.objects.create(action=action, titre=activite_titre, type=activite_type, indicateur_label=indicateur_label, indicateur_reference=indicateur_reference, cibles=cibles, couts=couts, point_focal=point_focal)

                        # Passer à l'activité suivante
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

        # Gestion des effets, produits, actions et activités
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