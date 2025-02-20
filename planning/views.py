# Modules Django
import json  # Pour traiter les champs JSON
from django.shortcuts import render, get_object_or_404, redirect
# Imports spécifiques au projet
from .models import PlanAction, Effet, Produit, Action, Activite

## Plan d'Actions
def plan_action_list(request):
    plans = PlanAction.objects.all()
    return render(request, 'planning/plan_action_list.html', {'plans': plans})

def plan_action_detail(request, id):
    plan = PlanAction.objects.get(id=id)

    # Récupérer les types d'activités et les années disponibles
    activity_types = ['Investissement', 'Réformes', 'Autre']  # Exemples de types
    available_years = [plan.annee_debut + i for i in range(plan.horizon + 1)]
    available_effects = Effet.objects.all()  # Récupérer tous les effets
    available_products = Produit.objects.all()  # Récupérer tous les produits
    available_actions = Action.objects.all()  # Récupérer toutes les actions
    available_structures = Activite.objects.values_list('point_focal__program', flat=True).distinct()

    # Récupérer les filtres envoyés par l'utilisateur
    selected_types = request.GET.getlist('type')  # Liste des types sélectionnés
    selected_years = request.GET.getlist('annee')  # Liste des années sélectionnées
    selected_effects = request.GET.getlist('effet')  # Liste des effets sélectionnés
    selected_products = request.GET.getlist('produit')  # Liste des produits sélectionnés
    selected_actions = request.GET.getlist('action')  # Liste des actions sélectionnées
    selected_structures = request.GET.getlist('structure')  # Liste des structures sélectionnées

    # Appliquer les filtres : si des types ou des années sont sélectionnés
    activites = Activite.objects.all()

    if selected_types:
        activites = activites.filter(type__in=selected_types)
    if selected_years:
        activites = activites.filter(annee__in=selected_years)
    if selected_effects:
        activites = activites.filter(effet__in=selected_effects)
    if selected_products:
        activites = activites.filter(produit__in=selected_products)
    if selected_actions:
        activites = activites.filter(action__in=selected_actions)
    if selected_structures:
        activites = activites.filter(structure__in=selected_structures)

    # Regroupement des activités par année
    activites_by_year = {}
    for activite in activites:
        if activite.annee not in activites_by_year:
            activites_by_year[activite.annee] = []
        activites_by_year[activite.annee].append({
            'titre': activite.titre,
            'indicator': activite.indicator,
            'reference': activite.reference,
            'cout_total': activite.get_cout_total,
            'type': activite.type,
            'structure': activite.structure,
            'effet': activite.effet.titre if activite.effet else "N/A",
            'produit': activite.produit.titre if activite.produit else "N/A",
            'action': activite.action.titre if activite.action else "N/A",
        })

    return render(request, 'plan_detail.html', {
        'plan': plan,
        'activites_by_year': activites_by_year,
        'activity_types': activity_types,
        'available_years': available_years,
        'available_effects': available_effects,
        'available_products': available_products,
        'available_actions': available_actions,
        'available_structures': available_structures,
        'selected_types': selected_types,
        'selected_years': selected_years,
        'selected_effects': selected_effects,
        'selected_products': selected_products,
        'selected_actions': selected_actions,
        'selected_structures': selected_structures,
    })

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