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
from django.core.exceptions import ValidationError
from django.db import transaction
import logging

logger = logging.getLogger(__name__)



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

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import PlanAction, Effet, Produit, Action, Activite

def plan_action_detail(request, id):
    plan = get_object_or_404(PlanAction, id=id)

    # Données initiales pour le rendu du template
    effets = Effet.objects.filter(plan=plan)
    produits = Produit.objects.filter(effet__plan=plan).select_related('effet')
    actions = Action.objects.filter(produit__effet__plan=plan).select_related('produit__effet')
    activites = Activite.objects.filter(action__produit__effet__plan=plan).select_related('action__produit__effet', 'point_focal')
    types = list(set(activite.type or "N/A" for activite in activites))
    structures = list(set(activite.point_focal.entity if activite.point_focal and hasattr(activite.point_focal, 'entity') else "N/A" for activite in activites))
    annees = [str(plan.annee_debut + i) for i in range(plan.horizon)] if plan.annee_debut and plan.horizon else []

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Récupérer les filtres depuis la requête GET
            effets_selectionnes = request.GET.getlist('effet')
            produits_selectionnes = request.GET.getlist('produit')
            actions_selectionnees = request.GET.getlist('action')
            types_selectionnes = request.GET.getlist('type')
            structures_selectionnees = request.GET.getlist('structure')
            annees_selectionnees = request.GET.getlist('annee')

            # Filtrer les effets
            filtered_effets = effets
            if effets_selectionnes:
                filtered_effets = filtered_effets.filter(titre__in=effets_selectionnes)
                produits = produits.filter(effet__titre__in=effets_selectionnes)
                actions = actions.filter(produit__effet__titre__in=effets_selectionnes)
                activites = activites.filter(action__produit__effet__titre__in=effets_selectionnes)

            # Filtrer les produits
            if produits_selectionnes:
                produits = produits.filter(titre__in=produits_selectionnes)
                actions = actions.filter(produit__titre__in=produits_selectionnes)
                activites = activites.filter(action__produit__titre__in=produits_selectionnes)

            # Filtrer les actions
            if actions_selectionnees:
                actions = actions.filter(titre__in=actions_selectionnees)
                activites = activites.filter(action__titre__in=actions_selectionnees)

            # Filtrer les activités
            if types_selectionnes:
                activites = activites.filter(type__in=types_selectionnes)
            if structures_selectionnees:
                activites = activites.filter(point_focal__entity__in=structures_selectionnees)

            # Filtrer les années
            filtered_annees = annees
            if annees_selectionnees:
                filtered_annees = [annee for annee in annees if annee in annees_selectionnees]

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
                                    'realisation': activite.realisation,
                                    'etat_avancement': activite.etat_avancement,
                                    'commentaire': activite.commentaire,
                                    'status': activite.status,
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

            # Mettre à jour les filtres dépendants
            types = list(set(activite.type or 'N/A' for activite in activites))
            structures = list(set(activite.point_focal.entity if activite.point_focal and hasattr(activite.point_focal, 'entity') else 'N/A' for activite in activites))

            data = {
                'effets': effets_data,
                'produits': [{'id': p.id, 'titre': p.titre, 'couts': p.couts} for p in produits],
                'actions': [{'id': a.id, 'titre': a.titre, 'couts': a.couts} for a in actions],
                'activites': [
                    {
                        'id': a.id,
                        'titre': a.titre,
                        'type': a.type or 'N/A',
                        'couts': a.couts,
                        'cibles': a.cibles,
                        'realisation': a.realisation,
                        'etat_avancement': a.etat_avancement,
                        'commentaire': a.commentaire,
                        'status': a.status,
                        'indicateur_label': a.indicateur_label,
                        'indicateur_reference': a.indicateur_reference
                    } for a in activites
                ],
                'types': types,
                'structures': structures,
                'annees': filtered_annees,
                'annee_debut': plan.annee_debut
            }

            return JsonResponse(data, safe=False)

        except Exception as e:
            print(f"🚨 Erreur lors du filtrage: {str(e)}")
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
        logger.debug(f"Contenu complet de request.POST : {request.POST}")
        try:
            with transaction.atomic():
                # 1. Création du PlanAction
                titre = request.POST.get('titre')
                impact = request.POST.get('impact')
                annee_debut = int(request.POST.get('annee_depart', 2025))
                horizon = int(request.POST.get('horizon', 1))
                logger.debug(f"PlanAction - titre: {titre}, impact: {impact}, annee_debut: {annee_debut}, horizon: {horizon}")

                if not titre or not impact:
                    raise ValueError("Le titre et l'impact sont requis.")
                if horizon <= 0:
                    raise ValueError("L'horizon doit être un nombre positif.")

                # Calcul de la référence pour PlanAction (ex: PA1, PA2, etc.)
                last_plan = PlanAction.objects.order_by('-id').first()
                plan_ref_number = int(last_plan.reference[2:]) + 1 if last_plan and last_plan.reference else 1
                plan_reference = f"PA{plan_ref_number}"

                plan_action = PlanAction(
                    titre=titre,
                    impact=impact,
                    annee_debut=annee_debut,
                    horizon=horizon,
                    reference=plan_reference,  # Attribution explicite
                )
                plan_action.save()
                logger.debug(f"PlanAction créé avec ID: {plan_action.id}, reference: {plan_action.reference}, couts: {plan_action.couts}")

                # 2. Traitement des Effets
                effet_count = 0
                while f'effet_titre_{effet_count + 1}' in request.POST:
                    effet_count += 1
                    effet_titre = request.POST.get(f'effet_titre_{effet_count}')
                    logger.debug(f"Effet {effet_count} - titre: {effet_titre}")
                    if not effet_titre:
                        raise ValueError(f"Le titre de l'effet {effet_count} est requis.")
                    
                    # Référence pour Effet (ex: 1, 2, etc. sous PA1)
                    effet_reference = str(effet_count)

                    effet = Effet(
                        plan=plan_action,
                        titre=effet_titre,
                        reference=effet_reference,  # Attribution explicite
                    )
                    effet.save()
                    logger.debug(f"Effet {effet_count} créé avec ID: {effet.id}, reference: {effet.reference}, couts: {effet.couts}")

                    # 3. Traitement des Produits
                    produit_count = 0
                    while f'produit_titre_{effet_count}_{produit_count + 1}' in request.POST:
                        produit_count += 1
                        produit_titre = request.POST.get(f'produit_titre_{effet_count}_{produit_count}')
                        logger.debug(f"Produit {effet_count}.{produit_count} - titre: {produit_titre}")
                        if not produit_titre:
                            raise ValueError(f"Le titre du produit {effet_count}.{produit_count} est requis.")
                        
                        # Référence pour Produit (ex: 1.1, 1.2, etc.)
                        produit_reference = f"{effet.reference}.{produit_count}"

                        produit = Produit(
                            effet=effet,
                            titre=produit_titre,
                            reference=produit_reference,  # Attribution explicite
                        )
                        produit.save()
                        logger.debug(f"Produit {effet_count}.{produit_count} créé avec ID: {produit.id}, reference: {produit.reference}, couts: {produit.couts}")

                        # 4. Traitement des Actions
                        action_count = 0
                        while f'action_titre_{effet_count}_{produit_count}_{action_count + 1}' in request.POST:
                            action_count += 1
                            action_titre = request.POST.get(f'action_titre_{effet_count}_{produit_count}_{action_count}')
                            logger.debug(f"Action {effet_count}.{produit_count}.{action_count} - titre: {action_titre}")
                            if not action_titre:
                                raise ValueError(f"Le titre de l'action {effet_count}.{produit_count}.{action_count} est requis.")
                            
                            # Référence pour Action (ex: 1.1.1, 1.1.2, etc.)
                            action_reference = f"{produit.reference}.{action_count}"

                            action = Action(
                                produit=produit,
                                titre=action_titre,
                                reference=action_reference,  # Attribution explicite
                            )
                            action.save()
                            logger.debug(f"Action {effet_count}.{produit_count}.{action_count} créé avec ID: {action.id}, reference: {action.reference}, couts: {action.couts}")

                            # 5. Traitement des Activités
                            activite_count = 0
                            while f'activite_titre_{effet_count}_{produit_count}_{action_count}_{activite_count + 1}' in request.POST:
                                activite_count += 1
                                activite_titre = request.POST.get(f'activite_titre_{effet_count}_{produit_count}_{action_count}_{activite_count}')
                                activite_type = request.POST.get(f'activite_type_{effet_count}_{produit_count}_{action_count}_{activite_count}')
                                indicateur_label = request.POST.get(f'indicateur_label_{effet_count}_{produit_count}_{action_count}_{activite_count}')
                                indicateur_reference = request.POST.get(f'indicateur_reference_{effet_count}_{produit_count}_{action_count}_{activite_count}')
                                logger.debug(f"Activité {effet_count}.{produit_count}.{action_count}.{activite_count} - titre: {activite_titre}, type: {activite_type}, indicateur_label: {indicateur_label}, indicateur_reference: {indicateur_reference}")

                                if not all([activite_titre, activite_type, indicateur_label, indicateur_reference]):
                                    raise ValueError(f"Les champs de l'activité {effet_count}.{produit_count}.{action_count}.{activite_count} doivent être remplis.")

                                # Référence pour Activité (ex: 1.1.1.1, 1.1.1.2, etc.)
                                activite_reference = f"{action.reference}.{activite_count}"

                                # Récupération des cibles, coûts et périodes
                                activite_couts = []
                                activite_cibles = []
                                activite_periodes = []
                                for i in range(horizon):
                                    cout = request.POST.get(f'cout_{effet_count}_{produit_count}_{action_count}_{activite_count}_{i}', '0')
                                    activite_couts.append(float(cout) if cout else 0.0)
                                    cible = request.POST.get(f'cible_{effet_count}_{produit_count}_{action_count}_{activite_count}_{i}', '')
                                    activite_cibles.append(cible if cible else None)
                                    periodes = []
                                    for t in range(1, 5):
                                        if request.POST.get(f'periode_{effet_count}_{produit_count}_{action_count}_{activite_count}_{i}_T{t}'):
                                            periodes.append(f'T{t}')
                                    activite_periodes.append(periodes)

                                activite = Activite(
                                    action=action,
                                    titre=activite_titre,
                                    type=activite_type,
                                    indicateur_label=indicateur_label,
                                    indicateur_reference=indicateur_reference,
                                    point_focal=request.user,
                                    responsable=None,  # À ajuster selon votre logique
                                    couts=activite_couts,
                                    cibles=activite_cibles,
                                    periodes_execution=activite_periodes,
                                    reference=activite_reference,  # Attribution explicite
                                )
                                activite.save(user=request.user)
                                logger.debug(f"Activité {effet_count}.{produit_count}.{action_count}.{activite_count} créé avec ID: {activite.id}, reference: {activite.reference}, couts: {activite.couts}, cibles: {activite.cibles}, periodes: {activite.periodes_execution}")

                messages.success(request, f"Plan d'action '{plan_action.titre}' créé avec succès (Référence: {plan_action.reference}).")
                logger.debug("Plan d'action créé avec succès, redirection vers 'plan_action_list'")
                return redirect('plan_action_list')

        except ValueError as ve:
            logger.error(f"Erreur de validation : {str(ve)}")
            messages.error(request, f"Erreur de validation : {str(ve)}")
            return render(request, 'planning/add_plan_action.html', {})
        except Exception as e:
            logger.error(f"Erreur inattendue : {str(e)}", exc_info=True)
            messages.error(request, f"Erreur lors de la création du plan d'action : {str(e)}")
            return render(request, 'planning/add_plan_action.html', {})
        
    logger.debug("Requête GET : Affichage du formulaire vide")
    return render(request, 'planning/add_plan_action.html', {})

def edit_plan_action(request, id):
    plan_action = get_object_or_404(PlanAction, id=id)

    if request.method == 'POST':
        logger.debug(f"Contenu complet de request.POST : {request.POST}")
        try:
            with transaction.atomic():
                # 1. Mise à jour du PlanAction
                titre = request.POST.get('titre')
                impact = request.POST.get('impact')
                annee_debut = int(request.POST.get('annee_depart', plan_action.annee_debut))
                horizon = int(request.POST.get('horizon', plan_action.horizon))
                logger.debug(f"PlanAction - titre: {titre}, impact: {impact}, annee_debut: {annee_debut}, horizon: {horizon}")

                if not titre or not impact:
                    raise ValueError("Le titre et l'impact sont requis.")
                if horizon <= 0:
                    raise ValueError("L'horizon doit être un nombre positif.")

                plan_action.titre = titre
                plan_action.impact = impact
                plan_action.annee_debut = annee_debut
                plan_action.horizon = horizon
                plan_action.save()
                logger.debug(f"PlanAction mis à jour avec ID: {plan_action.id}, reference: {plan_action.reference}, couts: {plan_action.couts}")

                # 2. Traitement des Effets
                effet_count = 0
                existing_effets = {effet.reference: effet for effet in Effet.objects.filter(plan=plan_action)}

                while f'effet_titre_{effet_count + 1}' in request.POST:
                    effet_count += 1
                    effet_titre = request.POST.get(f'effet_titre_{effet_count}')
                    effet_ref = str(effet_count)
                    logger.debug(f"Effet {effet_count} - titre: {effet_titre}")
                    if not effet_titre:
                        raise ValueError(f"Le titre de l'effet {effet_count} est requis.")

                    if effet_ref in existing_effets:
                        effet = existing_effets[effet_ref]
                        effet.titre = effet_titre
                        effet.save()
                        logger.debug(f"Effet {effet_count} mis à jour avec ID: {effet.id}, reference: {effet.reference}")
                    else:
                        effet = Effet(
                            plan=plan_action,
                            titre=effet_titre,
                            reference=effet_ref,
                        )
                        effet.save()
                        logger.debug(f"Effet {effet_count} créé avec ID: {effet.id}, reference: {effet.reference}")

                    # 3. Traitement des Produits
                    produit_count = 0
                    existing_produits = {produit.reference: produit for produit in Produit.objects.filter(effet=effet)}

                    while f'produit_titre_{effet_count}_{produit_count + 1}' in request.POST:
                        produit_count += 1
                        produit_titre = request.POST.get(f'produit_titre_{effet_count}_{produit_count}')
                        produit_ref = f"{effet_ref}.{produit_count}"
                        logger.debug(f"Produit {effet_count}.{produit_count} - titre: {produit_titre}")
                        if not produit_titre:
                            raise ValueError(f"Le titre du produit {effet_count}.{produit_count} est requis.")

                        if produit_ref in existing_produits:
                            produit = existing_produits[produit_ref]
                            produit.titre = produit_titre
                            produit.save()
                            logger.debug(f"Produit {effet_count}.{produit_count} mis à jour avec ID: {produit.id}, reference: {produit.reference}")
                        else:
                            produit = Produit(
                                effet=effet,
                                titre=produit_titre,
                                reference=produit_ref,
                            )
                            produit.save()
                            logger.debug(f"Produit {effet_count}.{produit_count} créé avec ID: {produit.id}, reference: {produit.reference}")

                        # 4. Traitement des Actions
                        action_count = 0
                        existing_actions = {action.reference: action for action in Action.objects.filter(produit=produit)}

                        while f'action_titre_{effet_count}_{produit_count}_{action_count + 1}' in request.POST:
                            action_count += 1
                            action_titre = request.POST.get(f'action_titre_{effet_count}_{produit_count}_{action_count}')
                            action_ref = f"{produit_ref}.{action_count}"
                            logger.debug(f"Action {effet_count}.{produit_count}.{action_count} - titre: {action_titre}")
                            if not action_titre:
                                raise ValueError(f"Le titre de l'action {effet_count}.{produit_count}.{action_count} est requis.")

                            if action_ref in existing_actions:
                                action = existing_actions[action_ref]
                                action.titre = action_titre
                                action.save()
                                logger.debug(f"Action {effet_count}.{produit_count}.{action_count} mis à jour avec ID: {action.id}, reference: {action.reference}")
                            else:
                                action = Action(
                                    produit=produit,
                                    titre=action_titre,
                                    reference=action_ref,
                                )
                                action.save()
                                logger.debug(f"Action {effet_count}.{produit_count}.{action_count} créé avec ID: {action.id}, reference: {action.reference}")

                            # 5. Traitement des Activités
                            activite_count = 0
                            existing_activites = {activite.reference: activite for activite in Activite.objects.filter(action=action)}

                            while f'activite_titre_{effet_count}_{produit_count}_{action_count}_{activite_count + 1}' in request.POST:
                                activite_count += 1
                                activite_titre = request.POST.get(f'activite_titre_{effet_count}_{produit_count}_{action_count}_{activite_count}')
                                activite_type = request.POST.get(f'activite_type_{effet_count}_{produit_count}_{action_count}_{activite_count}')
                                indicateur_label = request.POST.get(f'indicateur_label_{effet_count}_{produit_count}_{action_count}_{activite_count}')
                                indicateur_reference = request.POST.get(f'indicateur_reference_{effet_count}_{produit_count}_{action_count}_{activite_count}')
                                activite_ref = f"{action_ref}.{activite_count}"
                                logger.debug(f"Activité {effet_count}.{produit_count}.{action_count}.{activite_count} - titre: {activite_titre}, type: {activite_type}, indicateur_label: {indicateur_label}, indicateur_reference: {indicateur_reference}")

                                if not all([activite_titre, activite_type, indicateur_label, indicateur_reference]):
                                    raise ValueError(f"Les champs de l'activité {effet_count}.{produit_count}.{action_count}.{activite_count} doivent être remplis.")

                                # Récupération des cibles, coûts et périodes
                                activite_couts = []
                                activite_cibles = []
                                activite_periodes = []
                                for i in range(horizon):
                                    cout = request.POST.get(f'cout_{effet_count}_{produit_count}_{action_count}_{activite_count}_{i}', '0')
                                    activite_couts.append(float(cout) if cout else 0.0)
                                    cible = request.POST.get(f'cible_{effet_count}_{produit_count}_{action_count}_{activite_count}_{i}', '')
                                    activite_cibles.append(cible if cible else None)
                                    periodes = []
                                    for t in range(1, 5):
                                        if request.POST.get(f'periode_{effet_count}_{produit_count}_{action_count}_{activite_count}_{i}_T{t}'):
                                            periodes.append(f'T{t}')
                                    activite_periodes.append(periodes)

                                if activite_ref in existing_activites:
                                    activite = existing_activites[activite_ref]
                                    activite.titre = activite_titre
                                    activite.type = activite_type
                                    activite.indicateur_label = indicateur_label
                                    activite.indicateur_reference = indicateur_reference
                                    activite.couts = activite_couts
                                    activite.cibles = activite_cibles
                                    activite.periodes_execution = activite_periodes
                                    activite.save(user=request.user)
                                    logger.debug(f"Activité {effet_count}.{produit_count}.{action_count}.{activite_count} mis à jour avec ID: {activite.id}, reference: {activite.reference}")
                                else:
                                    activite = Activite(
                                        action=action,
                                        titre=activite_titre,
                                        type=activite_type,
                                        indicateur_label=indicateur_label,
                                        indicateur_reference=indicateur_reference,
                                        point_focal=request.user,
                                        responsable=None,  # À ajuster selon votre logique
                                        couts=activite_couts,
                                        cibles=activite_cibles,
                                        periodes_execution=activite_periodes,
                                        reference=activite_ref,
                                    )
                                    activite.save(user=request.user)
                                    logger.debug(f"Activité {effet_count}.{produit_count}.{action_count}.{activite_count} créé avec ID: {activite.id}, reference: {activite.reference}")

                messages.success(request, f"Plan d'action '{plan_action.titre}' modifié avec succès (Référence: {plan_action.reference}).")
                logger.debug("Plan d'action modifié avec succès, redirection vers 'plan_action_list'")
                return redirect('plan_action_list')

        except ValueError as ve:
            logger.error(f"Erreur de validation : {str(ve)}")
            messages.error(request, f"Erreur de validation : {str(ve)}")
            return render(request, 'planning/edit_plan_action.html', {'plan_action': plan_action})
        except Exception as e:
            logger.error(f"Erreur inattendue : {str(e)}", exc_info=True)
            messages.error(request, f"Erreur lors de la modification du plan d'action : {str(e)}")
            return render(request, 'planning/edit_plan_action.html', {'plan_action': plan_action})

    logger.debug("Requête GET : Affichage du formulaire pré-rempli")
    context = {
        'plan_action': plan_action,
        'effets': Effet.objects.filter(plan=plan_action).order_by('reference'),
        'produits': Produit.objects.filter(effet__plan=plan_action).order_by('reference'),
        'actions': Action.objects.filter(produit__effet__plan=plan_action).order_by('reference'),
        'activites': Activite.objects.filter(action__produit__effet__plan=plan_action).order_by('reference'),
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

    if not (is_responsable or is_point_focal):
        messages.error(request, "Cette page est réservée au point focal et au responsable de la structure.")
        return render(request, 'planning/access_denied.html', {'plan': plan})

    annee = int(request.GET.get('annee', plan.annee_debut))
    index = annee - plan.annee_debut
    if index < 0 or index >= plan.horizon:
        messages.error(request, "Année invalide.")
        return render(request, 'planning/error.html', {'message': "Année invalide."})

    # Filtrer les activités par plan et entité
    filters = Q(action__produit__effet__plan=plan)
    filters &= (Q(point_focal__entity=entity) | Q(responsable__entity=entity))
    
    activites = Activite.objects.filter(filters).distinct()

    if request.method == 'POST':
        data = request.POST
        activite = get_object_or_404(Activite, id=data.get('activite_id'))

        # Vérifier que l'activité appartient à l'entité
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

        if 'save' in data and (is_responsable or is_point_focal):
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

        return JsonResponse({'success': False, 'message': 'Action non autorisée'})

    # Préparer les données pour l'affichage
    activites_list = []
    for a in activites:
        horizon = plan.horizon
        for attr in ['realisation', 'matrix_status', 'couts', 'cibles']:
            if len(getattr(a, attr)) != horizon:
                setattr(a, attr, ["" if attr == 'realisation' else 'En cours' if attr == 'matrix_status' else 0.0 if attr == 'couts' else None] * horizon)
                a.save()

        activites_list.append({
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
        'activites': activites_list,
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