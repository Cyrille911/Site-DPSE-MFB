# Modules Django
import json  # Pour traiter les champs JSON
from django.shortcuts import render, get_object_or_404, redirect
from .models import PlanAction, Effet, Produit, Action, Activite, ActiviteLog
from django.http import JsonResponse
from django.db.models import Q
from datetime import datetime
from reversion import revisions as reversion
from django.contrib import messages
from django.core.paginator import Paginator
from .forms import PaoStatusForm  # Import du formulaire


def pppbse_gar(request):
    return render(request, 'planning/pppbse_gar.html')

## Plan d'Actions
def plan_action_list(request):
    plans = PlanAction.objects.all()  # Ou filtre selon tes besoins
    is_member = request.user.is_authenticated  # Simplifié, ajuste selon ta logique
    context = {
        'plans': plans,
        'is_member': is_member,
    }
    return render(request, 'planning/plan_action_list.html', context)

def plan_action_detail(request, id):
    plan = get_object_or_404(PlanAction, id=id)

    # Données initiales
    effets = Effet.objects.filter(plan=plan)
    produits = Produit.objects.filter(effet__plan=plan).select_related('effet')
    actions = Action.objects.filter(produit__effet__plan=plan).select_related('produit__effet')
    activites = Activite.objects.filter(action__produit__effet__plan=plan).select_related('action__produit__effet')
    types = list(set(activite.type if activite.type else "N/A" for activite in activites))
    structures = list(set(activite.point_focal.entity if activite.point_focal and hasattr(activite.point_focal, 'entity') else "N/A" for activite in activites))
    annees = [str(plan.annee_debut + i) for i in range(plan.horizon)] if plan.annee_debut and plan.horizon else []

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            effets_selectionnes = request.GET.getlist('effet')
            produits_selectionnes = request.GET.getlist('produit')
            actions_selectionnees = request.GET.getlist('action')
            types_selectionnes = request.GET.getlist('type')
            structures_selectionnees = request.GET.getlist('structure')
            annees_selectionnees = request.GET.getlist('annee')

            # Filtrer les données en cascade
            filtered_effets = effets
            if effets_selectionnes:
                filtered_effets = effets.filter(titre__in=effets_selectionnes)
                produits = produits.filter(effet__titre__in=effets_selectionnes)
                actions = actions.filter(produit__effet__titre__in=effets_selectionnes)
                activites = activites.filter(action__produit__effet__titre__in=effets_selectionnes)

            if produits_selectionnes:
                produits = produits.filter(titre__in=produits_selectionnes)
                actions = actions.filter(produit__titre__in=produits_selectionnes)
                activites = activites.filter(action__produit__titre__in=produits_selectionnes)

            if actions_selectionnees:
                actions = actions.filter(titre__in=actions_selectionnees)
                activites = activites.filter(action__titre__in=actions_selectionnees)

            if types_selectionnes:
                activites = activites.filter(type__in=types_selectionnes)

            if structures_selectionnees:
                activites = activites.filter(point_focal__entity__in=structures_selectionnees)

            if annees_selectionnees:
                annees = annees_selectionnees

            # Construire la structure hiérarchique pour la réponse JSON
            effets_data = []
            for effet in filtered_effets:
                effet_produits = produits.filter(effet=effet)
                produits_data = []
                for produit in effet_produits:
                    produit_actions = actions.filter(produit=produit)
                    actions_data = []
                    for action in produit_actions:
                        action_activites = activites.filter(action=action)
                        actions_data.append({
                            'id': action.id,
                            'titre': action.titre,
                            'couts': action.couts,
                            'activites': [
                                {
                                    'id': activite.id,
                                    'titre': activite.titre,
                                    'type': activite.type or 'N/A',
                                    'couts': activite.couts,
                                    'cibles': activite.cibles,
                                    'realisation': activite.realisation,  # Ajouté
                                    'etat_avancement': activite.etat_avancement,  # Ajouté
                                    'commentaire': activite.commentaire,  # Ajouté
                                    'status': activite.status,  # Ajouté
                                    'indicateur_label': activite.indicateur_label,
                                    'indicateur_reference': activite.indicateur_reference,
                                    'structure': activite.point_focal.entity if activite.point_focal and hasattr(activite.point_focal, 'entity') else 'N/A',
                                    'programme': activite.point_focal.program if activite.point_focal and hasattr(activite.point_focal, 'program') else 'N/A'
                                } for activite in action_activites
                            ]
                        })
                    produits_data.append({
                        'id': produit.id,
                        'titre': produit.titre,
                        'couts': produit.couts,
                        'actions': actions_data
                    })
                effets_data.append({
                    'id': effet.id,
                    'titre': effet.titre,
                    'couts': effet.couts,
                    'produits': produits_data
                })

            data = {
                'effets': effets_data,
                'produits': list(produits.values('id', 'titre', 'couts')),
                'actions': list(actions.values('id', 'titre', 'couts')),
                'activites': list(activites.values('id', 'titre', 'type', 'couts', 'cibles', 'realisation', 'etat_avancement', 'commentaire', 'status', 'indicateur_label', 'indicateur_reference')),
                'types': types,
                'structures': structures,
                'annees': annees,
                'annee_debut': plan.annee_debut
            }

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
        'types': types,
        'structures': structures,
        'annees': annees,
        'annee_debut': plan.annee_debut,
        'horizon': plan.horizon
    })

def add_plan_action(request):
    if request.method == 'POST':
        titre = request.POST.get('titre')
        horizon = request.POST.get('horizon')
        impact = request.POST.get('impact')
        annee_depart = request.POST.get('annee_depart')  # Ajouté car présent dans le template

        # Validation du champ horizon
        try:
            horizon = int(horizon)
            if horizon <= 0:
                raise ValueError("L'horizon doit être un entier positif.")
        except ValueError:
            return render(request, 'planning/add_plan_action.html', {'error': "L'horizon doit être un entier positif."})

        # Validation de l'année de départ
        try:
            annee_depart = int(annee_depart)
            if annee_depart < 2010:  # Contrainte du template
                raise ValueError("L'année de départ doit être >= 2010.")
        except ValueError:
            return render(request, 'planning/add_plan_action.html', {'error': "L'année de départ doit être >= 2010."})

        # Création du plan d'action
        plan = PlanAction.objects.create(
            titre=titre,
            horizon=horizon,
            impact=impact,
            annee_debut=annee_depart,
            couts=[0.0] * horizon  # Initialisation dynamique
        )

        # Gestion des effets, produits, actions et activités
        effet_index = 1
        while f"effet_titre_{effet_index}" in request.POST:
            effet_titre = request.POST.get(f"effet_titre_{effet_index}")
            effet = Effet.objects.create(plan=plan, titre=effet_titre, couts=[0.0] * horizon)

            produit_index = 1
            while f"produit_titre_{effet_index}.{produit_index}" in request.POST:
                produit_titre = request.POST.get(f"produit_titre_{effet_index}.{produit_index}")
                produit = Produit.objects.create(effet=effet, titre=produit_titre, couts=[0.0] * horizon)

                action_index = 1
                while f"action_titre_{effet_index}.{produit_index}.{action_index}" in request.POST:
                    action_titre = request.POST.get(f"action_titre_{effet_index}.{produit_index}.{action_index}")
                    action = Action.objects.create(produit=produit, titre=action_titre, couts=[0.0] * horizon)

                    activite_index = 1
                    while f"activite_titre_{effet_index}.{produit_index}.{action_index}.{activite_index}" in request.POST:
                        # Récupération des informations de l'activité
                        activite_titre = request.POST.get(f"activite_titre_{effet_index}.{produit_index}.{action_index}.{activite_index}")
                        activite_type = request.POST.get(f"activite_type_{effet_index}.{produit_index}.{action_index}.{activite_index}")
                        indicateur_label = request.POST.get(f"indicateur_label_{effet_index}.{produit_index}.{action_index}.{activite_index}")
                        indicateur_reference = request.POST.get(f"indicateur_reference_{effet_index}.{produit_index}.{action_index}.{activite_index}")

                        # Récupérer et valider les cibles et coûts
                        cibles = []
                        couts = []
                        for i in range(1, horizon + 1):
                            cible_valeur = request.POST.get(f"cible_{effet_index}.{produit_index}.{action_index}.{activite_index}[{i}]", "")
                            cout_valeur = request.POST.get(f"cout_{effet_index}.{produit_index}.{action_index}.{activite_index}[{i}]", "0")
                            cibles.append(cible_valeur if cible_valeur else None)
                            try:
                                couts.append(float(cout_valeur) if cout_valeur else 0.0)
                            except ValueError:
                                couts.append(0.0)

                        # Initialisation de realisation
                        realisation = [""] * horizon  # Liste vide de la bonne taille

                        # Création de l'activité
                        point_focal = request.user
                        Activite.objects.create(
                            action=action,
                            titre=activite_titre,
                            type=activite_type,
                            indicateur_label=indicateur_label,
                            indicateur_reference=indicateur_reference,
                            cibles=cibles,
                            realisation=realisation,  # Ajouté ici
                            couts=couts,
                            point_focal=point_focal
                        )

                        activite_index += 1
                    action_index += 1
                produit_index += 1
            effet_index += 1

        return redirect('plan_action_list')

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

def pao_list(request, plan_id):
    plan = get_object_or_404(PlanAction, id=plan_id)
    
    # Créer une liste de PAO à partir de statut_pao
    paos = [
        {
            'annee': plan.annee_debut + i,
            'statut': plan.statut_pao[i],
            'index': i
        }
        for i in range(plan.horizon)
    ]
    
    # Déterminer l'entité (entity) à partir de l'utilisateur connecté
    # Supposons que l'utilisateur a un attribut 'entity' (à adapter selon votre modèle)
    entity = getattr(request.user, 'entity', None)
    if not entity:
        # Si l'utilisateur n'a pas d'entité définie, utilisez une valeur par défaut ou une logique alternative
        entity = "DefaultEntity"  # À remplacer par une logique appropriée
    
    # Passer 'entity' au contexte du template
    return render(request, 'planning/pao_list.html', {
        'plan': plan,
        'paos': paos,
        'entity': entity
    })

def manage_activities(request, plan_id, entity):
    plan = get_object_or_404(PlanAction, id=plan_id)
    
    # Vérification des rôles
    is_responsable = request.user.groups.filter(name='Responsable').exists()
    is_point_focal = request.user.groups.filter(name='PointFocal').exists()
    is_suiveur_evaluateur = request.user.groups.filter(name='SuiveurEvaluateur').exists()

    # Récupérer l'entité de l'utilisateur
    user_entity = getattr(request.user, 'entity', None)
    #if not user_entity:
        #messages.error(request, "Utilisateur sans entité définie.")
        #return render(request, 'planning/access_denied.html', {'plan': plan})

    #if is_suiveur_evaluateur or not (is_responsable or is_point_focal) or user_entity != entity:
        #messages.error(request, "Cette page est réservée au point focal et au responsable de la structure.")
        #return render(request, 'planning/access_denied.html', {'plan': plan})

    annee = int(request.GET.get('annee', plan.annee_debut))
    index = annee - plan.annee_debut
    if index < 0 or index >= plan.horizon:
        messages.error(request, "Année invalide.")
        return render(request, 'planning/error.html', {'message': "Année invalide."})

    filters = Q(action__produit__effet__plan=plan)
    if is_point_focal:
        filters &= Q(point_focal__entity=entity)
    if is_responsable:
        filters &= Q(responsable__entity=entity)

    activites = Activite.objects.filter(filters).select_related('point_focal', 'responsable')

    if request.method == 'POST':
        data = request.POST
        activite = get_object_or_404(Activite, id=data.get('activite_id'))

        activite_entity = getattr(activite.point_focal, 'entity', None) or getattr(activite.responsable, 'entity', None)
        if activite_entity != entity:
            return JsonResponse({'success': False, 'message': "Activité hors de votre structure."})

        # Préparer les données pour mise à jour
        old_data = {
            'etat_avancement': activite.etat_avancement,
            'realisation': activite.realisation[index],
            'commentaire': activite.commentaire,
        }
        new_data = {
            'etat_avancement': data.get('etat_avancement', old_data['etat_avancement']),
            'realisation': data.get('realisation', old_data['realisation']),
            'commentaire': data.get('commentaire', old_data['commentaire']),
        }

        # Comparer avant/après pour les logs
        changes = {k: {'avant': old_data[k], 'apres': new_data[k]} for k in old_data if old_data[k] != new_data[k]}

        if 'save' in data:
            activite.etat_avancement = new_data['etat_avancement']
            activite.realisation[index] = new_data['realisation']
            activite.commentaire = new_data['commentaire']
            activite.status = 'Draft'
            activite.matrix_status[index] = 'En cours'
            activite.save(user=request.user)
            if changes:
                ActiviteLog.objects.create(
                    activite=activite,
                    user=request.user,
                    modifications=changes,
                    statut_apres='Draft'
                )
            return JsonResponse({'success': True, 'message': 'Activité enregistrée'})

        elif 'validate' in data and is_responsable:
            activite.etat_avancement = new_data['etat_avancement']
            activite.realisation[index] = new_data['realisation']
            activite.commentaire = new_data['commentaire']
            activite.status = 'Submitted_SE'
            activite.matrix_status[index] = 'En cours'
            activite.save(user=request.user)
            if changes:
                ActiviteLog.objects.create(
                    activite=activite,
                    user=request.user,
                    modifications=changes,
                    statut_apres='Submitted_SE'
                )
            return JsonResponse({'success': True, 'message': 'Activité validée et soumise au SE'})

    activites_by_entity = {}
    for a in activites:
        horizon = plan.horizon
        for attr in ['realisation', 'matrix_status', 'couts', 'cibles']:
            if len(getattr(a, attr)) != horizon:
                setattr(a, attr, ["" if attr == 'realisation' else 'En cours' if attr == 'matrix_status' else 0.0 if attr == 'couts' else None] * horizon)
                a.save()

        entity_key = getattr(a.point_focal, 'entity', None) or getattr(a.responsable, 'entity', None) or 'Sans entité'
        activites_by_entity.setdefault(entity_key, []).append({
            'id': a.id,
            'titre': a.titre,
            'type': a.type,
            'etat_avancement': a.etat_avancement,
            'realisation': a.realisation[index],
            'cout': a.couts[index],
            'cible': a.cibles[index],
            'commentaire': a.commentaire,
            'commentaire_se': a.commentaire_se,
            'status': a.status,
            'matrix_status': a.matrix_status[index],
        })

    context = {
        'plan': plan,
        'annee': annee,
        'entity': entity,
        'activites_by_entity': {entity: activites_by_entity.get(entity, [])},
        'is_responsable': is_responsable,
        'is_point_focal': is_point_focal,
    }
    return render(request, 'planning/manage_activities.html', context)

def track_execution_list(request, plan_id):
    plan = get_object_or_404(PlanAction, id=plan_id)
    is_se = request.user.groups.filter(name='SuiveurEvaluateur').exists()

    # Vérification des permissions
    #if not is_se:
        #messages.error(request, "Seul un Suiveur Évaluateur peut accéder à cette page.")
        #return render(request, 'planning/access_denied.html', {'plan': plan})

    # Générer la liste des PAO par année avec leur statut
    paos = [
        {'annee': plan.annee_debut + i, 'statut': plan.statut_pao[i]}
        for i in range(plan.horizon)
    ]

    context = {
        'plan': plan,
        'paos': paos,
    }
    return render(request, 'planning/track_execution_list.html', context)

def track_execution_detail(request, plan_id):
    plan = get_object_or_404(PlanAction, id=plan_id)
    is_se = request.user.groups.filter(name='SuiveurEvaluateur').exists()

    #if not is_se:
        #messages.error(request, "Seul un Suiveur Évaluateur peut accéder à cette page.")
        #return render(request, 'planning/access_denied.html', {'plan': plan})

    # Récupérer l'année depuis les paramètres GET
    annee = request.GET.get('annee')
    if not annee or not annee.isdigit() or int(annee) < plan.annee_debut or int(annee) >= plan.annee_debut + plan.horizon:
        messages.error(request, "Année invalide pour ce plan.")
        return render(request, 'planning/error.html', {'message': "Année invalide pour ce plan."})

    annee = int(annee)
    index = annee - plan.annee_debut

    pao_statut = plan.statut_pao[index] if index < len(plan.statut_pao) else 'Non entamé'
    activites = Activite.objects.filter(
        action__produit__effet__plan=plan,
        status__in=['Pending_SE', 'Réalisé', 'Non réalisé', 'Supprimé', 'Reprogrammé', 'Rejeté']
    ).select_related('responsable', 'point_focal', 'action__produit__effet')

    has_submitted_activities = activites.exists()
    form = PaoStatusForm(initial={'statut': pao_statut}) if not has_submitted_activities else None

    if request.method == 'POST':
        data = request.POST

        if 'update_pao_status' in data and not has_submitted_activities:
            if index >= len(plan.statut_pao):
                plan.statut_pao.extend(['Non entamé'] * (index - len(plan.statut_pao) + 1))
            plan.statut_pao[index] = data.get('statut_pao')
            plan.save()
            messages.success(request, f"Statut du PAO {annee} mis à jour : {data.get('statut_pao')}")
            return render(request, 'planning/track_execution_detail.html', {
                'plan': plan,
                'annee': annee,
                'pao_statut': plan.statut_pao[index],
                'form': PaoStatusForm(initial={'statut': plan.statut_pao[index]}),
                'activites_by_entity': {},
                'is_se': True,
                'has_submitted_activities': has_submitted_activities,
            })

        elif 'update_activity' in data:
            activite = get_object_or_404(Activite, id=data.get('activite_id'))
            activite.status = data.get('status')
            activite.commentaire_se = data.get('commentaire_se')
            activite.save()
            return JsonResponse({'success': True, 'message': 'Activité mise à jour'})

        elif 'submit_back' in data:
            activite = get_object_or_404(Activite, id=data.get('activite_id'))
            activite.status = 'Draft'
            activite.save()
            return JsonResponse({'success': True, 'message': 'Activité renvoyée au responsable'})

        elif 'validate_to_matrix' in data:
            activite = get_object_or_404(Activite, id=data.get('activite_id'))
            activite.status = activite.status  # Statut final déjà défini
            activite.save()
            return JsonResponse({'success': True, 'message': 'Activité validée et envoyée à la matrice'})

    activites_by_entity = {}
    for a in activites:
        entity = (a.point_focal.entity if a.point_focal and hasattr(a.point_focal, 'entity') else 
                  a.responsable.entity if a.responsable and hasattr(a.responsable, 'entity') else 'Sans entité')
        if entity not in activites_by_entity:
            activites_by_entity[entity] = []
        activites_by_entity[entity].append({
            'id': a.id,
            'titre': a.titre,
            'type': a.type,
            'etat_avancement': a.etat_avancement,
            'realisation': a.realisation[index] if a.realisation and index < len(a.realisation) else '',
            'cout': a.couts[index] if a.couts and index < len(a.couts) else '',
            'cible': a.cibles[index] if a.cibles and index < len(a.cibles) else '',
            'commentaire': a.commentaire,
            'commentaire_se': a.commentaire_se,
            'status': a.status,
            'can_submit_to_matrix': a.status in ['Réalisé', 'Non réalisé', 'Supprimé', 'Reprogrammé', 'Rejeté'],
        })

    context = {
        'plan': plan,
        'annee': annee,
        'pao_statut': pao_statut,
        'form': form,
        'activites_by_entity': activites_by_entity,
        'is_se': True,
        'has_submitted_activities': has_submitted_activities,
    }
    return render(request, 'planning/track_execution_detail.html', context)
    
# Matrice complète du plan opérationnel (SE uniquement)
def operational_plan_matrix(request, plan_id, annee):
    # Récupérer le plan
    plan = get_object_or_404(PlanAction, id=plan_id)
    annees = [plan.annee_debut + i for i in range(plan.horizon)]
    annee_index = annees.index(annee) if annee in annees else 0

    # Récupérer les effets du plan
    effets = Effet.objects.filter(plan=plan)
    effets_data = []

    for effet in effets:
        produits_data = []
        # Utiliser effet_produit au lieu de produits
        for produit in effet.effet_produit.all():
            actions_data = []
            for action in produit.produit_action.all():  # related_name correct
                activites_data = []
                for activite in action.action_activite.all():  # related_name correct
                    horizon = plan.horizon
                    # Initialisation des listes si elles ne correspondent pas à l'horizon
                    if len(activite.realisation) != horizon:
                        activite.realisation = [""] * horizon
                        activite.save()
                    if len(activite.couts) != horizon:
                        activite.couts = [0.0] * horizon
                        activite.save()
                    if len(activite.cibles) != horizon:
                        activite.cibles = [None] * horizon
                        activite.save()
                    if len(activite.matrix_status) != horizon:  # Ajout pour matrix_status
                        activite.matrix_status = ["en cours"] * horizon
                        activite.save()

                    # Récupérer la dernière modification de matrix_status
                    last_matrix_change = activite.get_last_matrix_status_change()
                    activites_data.append({
                        'id': activite.id,
                        'titre': activite.titre,
                        'type': activite.type,
                        'indicateur_label': activite.indicateur_label,
                        'indicateur_reference': activite.indicateur_reference,
                        'cibles': activite.cibles,
                        'structure': (activite.point_focal.entity if activite.point_focal and hasattr(activite.point_focal, 'entity') else 
                                      activite.responsable.entity if activite.responsable and hasattr(activite.responsable, 'entity') else 'Sans entité'),
                        'couts': activite.couts,
                        'realisation': activite.realisation,
                        'etat_avancement': activite.etat_avancement,
                        'commentaire': activite.commentaire,
                        'commentaire_se': activite.commentaire_se,
                        'status': activite.status,
                        'matrix_status': activite.matrix_status if hasattr(activite, 'matrix_status') else [],
                        'last_modified_matrix_status': last_matrix_change.strftime('%Y-%m-%d %H:%M:%S') if last_matrix_change else 'Non défini',
                    })
                if activites_data:
                    actions_data.append({
                        'titre': action.titre,
                        'couts': [sum(a.couts[i] for a in action.action_activite.all() if i < len(a.couts)) for i in range(plan.horizon)],
                        'activites': activites_data,
                    })
            if actions_data:
                produits_data.append({
                    'titre': produit.titre,
                    'couts': [sum(a.couts[i] for a in produit.produit_action.all() for a in a.action_activite.all() if i < len(a.couts)) for i in range(plan.horizon)],
                    'actions': actions_data,
                })
        if produits_data:
            effets_data.append({
                'titre': effet.titre,
                'couts': [sum(a.couts[i] for a in effet.effet_produit.all() for a in a.produit_action.all() for a in a.action_activite.all() if i < len(a.couts)) for i in range(plan.horizon)],
                'produits': produits_data,
            })

    # Options de filtre
    produits = Produit.objects.filter(effet__plan=plan)
    actions = Action.objects.filter(produit__effet__plan=plan)
    types = set(a.type for a in Activite.objects.filter(action__produit__effet__plan=plan) if a.type)
    structures = set(a['structure'] for e in effets_data for p in e['produits'] for a in p['actions'] for a in a['activites'])

    # Réponse AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'impact': plan.impact,
            'effets': effets_data,
            'annees': annees,
            'annee_debut': plan.annee_debut,
            'plan_titre': plan.titre,
        })

    # Contexte pour le rendu initial
    context = {
        'plan': plan,
        'impact': plan.impact,
        'effets': effets_data,
        'effet_list': [{'id': e.id, 'titre': e.titre} for e in effets],
        'produit_list': [{'id': p.id, 'titre': p.titre} for p in produits],
        'action_list': [{'id': a.id, 'titre': a.titre} for a in actions],
        'types': list(types),
        'structures': list(structures),
        'annees': annees,
        'annee': annee,
    }
    return render(request, 'planning/operational_plan_matrix.html', context)

def hierarchy_review(request, plan_id):
    # Récupérer le PlanAction
    plan = get_object_or_404(PlanAction, id=plan_id)
    
    # Vérifier si l'utilisateur a le rôle hiérarchique
    is_hierarchy = request.user.groups.filter(name='Hierarchy').exists()
    #if not is_hierarchy:
        #return render(request, 'planning/access_denied.html', {'plan': plan})

    # Générer la liste des PAO par année
    paos = []
    for i in range(plan.horizon):
        annee = plan.annee_debut + i
        statut = plan.statut_pao[i] if i < len(plan.statut_pao) else "Non entamé"
        paos.append({
            'annee': annee,
            'statut': statut,
        })

    context = {
        'plan': plan,
        'paos': paos,
    }
    return render(request, 'planning/hierarchy_review.html', context)