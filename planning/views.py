# Modules Django
import json  # Pour traiter les champs JSON
from django.shortcuts import render, get_object_or_404, redirect
from .models import PlanAction, Effet, Produit, Action, Activite
from django.http import JsonResponse

## Liste des activiités par struture
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import PlanAction, Activite, Action

## Plan d'Actions
def plan_action_list(request):
    plans = PlanAction.objects.all()
    return render(request, 'planning/plan_action_list.html', {'plans':plans})

def plan_action_detail(request, id):

    plan = get_object_or_404(PlanAction, id=id)

    effets = Effet.objects.filter(plan=plan)
    produits = Produit.objects.filter(effet__plan=plan).select_related('effet')
    actions = Action.objects.filter(produit__effet__plan=plan).select_related('produit__effet')
    activites = Activite.objects.filter(action__produit__effet__plan=plan).select_related('action__produit__effet')

    print(f"Effets récupérés: {effets.count()}")
    print(f"Produits récupérés: {produits.count()}")
    print(f"Actions récupérées: {actions.count()}")
    print(f"Activités récupérées: {activites.count()}")

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            effets_selectionnes = request.GET.getlist('effet')
            produits_selectionnes = request.GET.getlist('produit')
            actions_selectionnees = request.GET.getlist('action')

            print("Effets sélectionnés:", effets_selectionnes)
            print("Produits sélectionnés:", produits_selectionnes)
            print("Actions sélectionnées:", actions_selectionnees)

            # Mise à jour dynamique des filtres
            if effets_selectionnes:
                produits = Produit.objects.filter(effet__titre__in=effets_selectionnes)
                actions = Action.objects.filter(produit__effet__titre__in=effets_selectionnes)
                activites = Activite.objects.filter(action__produit__effet__titre__in=effets_selectionnes)
                print("Produits après filtrage par effets:", list(produits.values_list('titre', flat=True)))

            if produits_selectionnes:
                actions = Action.objects.filter(produit__titre__in=produits_selectionnes)
                activites = Activite.objects.filter(action__produit__titre__in=produits_selectionnes)
                print("Actions après filtrage par produits:", list(actions.values_list('titre', flat=True)))

            if actions_selectionnees:
                activites = Activite.objects.filter(action__titre__in=actions_selectionnees)
                print("Activités après filtrage par actions:", list(activites.values_list('titre', flat=True)))

            # Gestion des types et structures
            types = [activite.type if activite.type else "N/A" for activite in activites]
            structures = [activite.point_focal.entity if activite.point_focal and activite.point_focal.entity else "N/A" for activite in activites]

            # Calcul des années avec coût nul
            annees = []
            for activite in activites:
                if hasattr(activite, 'couts') and isinstance(activite.couts, list):
                    annee_debut = getattr(activite.action.produit.effet.plan, 'annee_debut', None)
                    if annee_debut is not None:
                        annees.append([annee_debut + i for i, cout in enumerate(activite.couts) if cout == 0])
                    else:
                        print(f"⚠️ `annee_debut` manquant pour {activite}.")
                        annees.append([])
                else:
                    print(f"⚠️ `couts` manquant ou invalide pour {activite}.")
                    annees.append([])

            print("✅ Années générées pour chaque activité:", annees)

            data = {
                'effets': list(effets.values('id', 'titre')),
                'produits': list(produits.values('id', 'titre')),
                'actions': list(actions.values('id', 'titre')),
                'activites': list(activites.values('id', 'titre')),
                'types': types,
                'structures': structures,
                'annees': annees
            }

            print("Données renvoyées:", data)
            return JsonResponse(data, safe=False)

        except Exception as e:
            print("🚨 Erreur lors du filtrage:", str(e))
            return JsonResponse({"error": "Erreur interne", "details": str(e)}, status=500)

    return render(request, 'planning/plan_action_detail.html', {
        "plan": plan,
        "effets": effets,
        "produits": produits,
        "actions": actions,
        "activites": activites,
        'types': [activite.type if activite.type else "N/A" for activite in activites],
        'structures': [activite.point_focal.entity if activite.point_focal and activite.point_focal.entity else "N/A" for activite in activites],
        'annees': [
            [
                activite.action.produit.effet.plan.annee_debut + i
                for i, cout in enumerate(activite.couts) if cout == 0
            ]
            if hasattr(activite, 'couts') and activite.couts else []
            for activite in activites
        ],
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
        # Mise à jour des informations du plan
        plan.titre = request.POST.get('titre')
        plan.horizon = int(request.POST.get('horizon'))
        plan.impact = request.POST.get('impact')
        
        try:
            horizon = int(plan.horizon)
            if horizon <= 0:
                raise ValueError("L'horizon doit être un entier positif.")
        except ValueError:
            return render(request, 'planning/edit_plan_action.html', {
                'plan': plan,
                'error': "L'horizon doit être un entier positif."
            })
        
        plan.save()

        # Suppression des anciens effets pour les recréer
        plan.plan_effet.all().delete()

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
                        activite_type = request.POST.get(f"activite_type_{effet_index}.{produit_index}.{action_index}.{activite_index}")
                        indicateur_label = request.POST.get(f"indicateur_label_{effet_index}.{produit_index}.{action_index}.{activite_index}")
                        indicateur_reference = request.POST.get(f"indicateur_reference_{effet_index}.{produit_index}.{action_index}.{activite_index}")

                        cibles = []
                        couts = []
                        for i in range(1, horizon + 1):
                            cible_valeur = request.POST.get(f"cible_{effet_index}.{produit_index}.{action_index}.{activite_index}[{i}]", None)
                            cout_valeur = request.POST.get(f"cout_{effet_index}.{produit_index}.{action_index}.{activite_index}[{i}]", '0')
                            
                            cibles.append(cible_valeur if cible_valeur else '')
                            couts.append(float(cout_valeur) if cout_valeur else 0.0)

                        point_focal = request.user
                        Activite.objects.create(
                            action=action,
                            titre=activite_titre,
                            type=activite_type,
                            indicateur_label=indicateur_label,
                            indicateur_reference=indicateur_reference,
                            cibles=cibles,
                            couts=couts,
                            point_focal=point_focal
                        )
                        activite_index += 1
                    action_index += 1
                produit_index += 1
            effet_index += 1

        return redirect('plan_action_list')

    # Pré-remplissage des données existantes pour le GET
    context = {
        'plan': plan,
        'effets': plan.plan_effet.prefetch_related(
            'effet_produit__produit_action__action_activite'
        )
    }
    return render(request, 'planning/edit_plan_action.html', context)

@csrf_exempt
def task_list(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Utilisateur non authentifié'})

    if request.method == 'GET':
        # Récupérer toutes les activités où l'utilisateur est point focal
        activites = Activite.objects.filter(point_focal=request.user).select_related(
            'action__produit__effet__plan'
        )
        plans = PlanAction.objects.all().prefetch_related('plan_effet__effet_produit__produit_action')
        max_horizon = max(plan.horizon for plan in plans) if plans else 0
        # Utiliser une année de référence (par exemple, l'année minimale parmi les plans)
        annee_debut_base = min(plan.annee_debut for plan in plans) if plans else 2025

        context = {
            'activites': activites,
            'plans': plans,
            'max_horizon': max_horizon,
            'max_horizon_range': range(max_horizon),
            'annee_debut_base': annee_debut_base
        }
        return render(request, 'planning/task_list.html', context)

    elif request.method == 'POST':
        data = json.loads(request.body)
        activities = data.get('activities', [])

        for activity_data in activities:
            action_id = activity_data.get('action_id')
            activite_id = activity_data.get('id')
            is_new = activity_data.get('is_new', False)

            if is_new:
                try:
                    action = Action.objects.get(id=action_id)
                    Activite.objects.create(
                        action=action,
                        titre=activity_data['titre'],
                        type=activity_data['type'],
                        indicateur_label=activity_data['indicateur_label'],
                        indicateur_reference=activity_data['indicateur_reference'],
                        cibles=activity_data['cibles'],
                        couts=[0.0] * action.produit.effet.plan.horizon,  # Coûts initialisés à zéro
                        point_focal=request.user
                    )
                except Action.DoesNotExist:
                    return JsonResponse({'success': False, 'error': f"Action avec ID {action_id} non trouvée."})
            else:
                try:
                    activite = Activite.objects.get(id=activite_id, point_focal=request.user)
                    activite.titre = activity_data['titre']
                    activite.type = activity_data['type']
                    activite.indicateur_label = activity_data['indicateur_label']
                    activite.indicateur_reference = activity_data['indicateur_reference']
                    activite.cibles = activity_data['cibles']
                    activite.save()
                except Activite.DoesNotExist:
                    return JsonResponse({'success': False, 'error': f"Activité avec ID {activite_id} non trouvée ou vous n'êtes pas autorisé."})

        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})

@csrf_exempt
def delete_activite(request, activite_id):
    if request.method == 'DELETE':
        try:
            activite = Activite.objects.get(id=activite_id, point_focal=request.user)
            activite.delete()
            return JsonResponse({'success': True})
        except Activite.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Activité non trouvée ou vous n\'êtes pas autorisé.'})
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})