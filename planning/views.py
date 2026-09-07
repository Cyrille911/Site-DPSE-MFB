# Modules Django
from django.shortcuts import render, get_object_or_404, redirect
<<<<<<< HEAD
from .models import PlanAction, Axe, Effet, IndicateurEffet, Produit, IndicateurProduit, Action, Activite, ActiviteLog, PreuveRealisation
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import PaoStatusForm, PreuveRealisationForm
=======
from .models import PlanAction, Effet, Produit, Action, Activite, ActiviteLog, PreuveRealisation, QuarterlyReport
from django.core.exceptions import ValidationError
from .tasks import generate_quarterly_report
from django.http import JsonResponse
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import PaoStatusForm
>>>>>>> 9800f3858682969e9bcf877aa3d23c715dbb2ea2
from django.db import transaction
import logging

from users.models import User

logger = logging.getLogger(__name__)

def add_plan_action(request):

    is_authenticated = request.user.is_authenticated
    if not (is_authenticated):
        return render(request, 'planning/access_denied.html')
    
    is_pf_or_se = request.user.role in ['point_focal', 'suiveur_evaluateur']
    if not (is_pf_or_se):
        return render(request, 'planning/access_denied.html')
    
    if request.method == 'POST':
        logger.debug(f"Contenu complet de request.POST : {request.POST}")
        try:
            with transaction.atomic():
                # Création du PlanAction
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
                    reference=plan_reference,
                )
                plan_action.save()
                logger.debug(f"PlanAction créé avec ID: {plan_action.id}, reference: {plan_action.reference}, couts: {plan_action.couts}")

                # Traitement des Axes
                axe_count = 0
                while f'axe_titre_{axe_count + 1}' in request.POST:
                    axe_count += 1
                    axe_titre = request.POST.get(f'axe_titre_{axe_count}')
                    logger.debug(f"Axe {axe_count} - titre: {axe_titre}")
                    if not axe_titre:
                        raise ValueError(f"Le titre de l'axe {axe_count} est requis.")
                    
                    axe_reference = str(axe_count)
                    axe = Axe(
                        plan=plan_action,
                        titre=axe_titre,
                        reference=axe_reference,
                    )
                    axe.save()
                    logger.debug(f"Axe {axe_count} créé avec ID: {axe.id}, reference: {axe.reference}")

                    # Traitement des Effets
                    effet_count = 0
                    while f'effet_titre_{axe_count}_{effet_count + 1}' in request.POST:
                        effet_count += 1
                        effet_titre = request.POST.get(f'effet_titre_{axe_count}_{effet_count}')
                        logger.debug(f"Effet {axe_count}.{effet_count} - titre: {effet_titre}")
                        if not effet_titre:
                            raise ValueError(f"Le titre de l'effet {axe_count}.{effet_count} est requis.")
                        
                        effet_reference = f"{axe.reference}.{effet_count}"
                        effet = Effet(
                            axe=axe,
                            titre=effet_titre,
                            reference=effet_reference,
                        )
                        effet.save()
                        logger.debug(f"Effet {axe_count}.{effet_count} créé avec ID: {effet.id}, reference: {effet.reference}")

                        # Traitement des indicateurs d'effet
                        ind_effet_count = 0
                        while f'indicateur_effet_label_{axe_count}_{effet_count}_{ind_effet_count + 1}' in request.POST:
                            ind_effet_count += 1
                            ind_label = request.POST.get(f'indicateur_effet_label_{axe_count}_{effet_count}_{ind_effet_count}')
                            ind_ref = request.POST.get(f'indicateur_effet_reference_{axe_count}_{effet_count}_{ind_effet_count}', '')
                            if ind_label:
                                ind_cibles = []
                                for i in range(horizon):
                                    cible = request.POST.get(f'indicateur_effet_cible_{axe_count}_{effet_count}_{ind_effet_count}_{i}', '')
                                    ind_cibles.append(cible if cible else "")
                                IndicateurEffet.objects.create(
                                    effet=effet,
                                    label=ind_label,
                                    reference=ind_ref,
                                    cibles=ind_cibles,
                                )

                        # Traitement des Produits
                        produit_count = 0
                        while f'produit_titre_{axe_count}_{effet_count}_{produit_count + 1}' in request.POST:
                            produit_count += 1
                            produit_titre = request.POST.get(f'produit_titre_{axe_count}_{effet_count}_{produit_count}')
                            logger.debug(f"Produit {axe_count}.{effet_count}.{produit_count} - titre: {produit_titre}")
                            if not produit_titre:
                                raise ValueError(f"Le titre du produit {axe_count}.{effet_count}.{produit_count} est requis.")
                            
                            produit_reference = f"{effet.reference}.{produit_count}"
                            produit = Produit(
                                effet=effet,
                                titre=produit_titre,
                                reference=produit_reference,
                            )
                            produit.save()
                            logger.debug(f"Produit {axe_count}.{effet_count}.{produit_count} créé avec ID: {produit.id}, reference: {produit.reference}")

                            # Traitement des indicateurs de produit
                            ind_produit_count = 0
                            while f'indicateur_produit_label_{axe_count}_{effet_count}_{produit_count}_{ind_produit_count + 1}' in request.POST:
                                ind_produit_count += 1
                                ind_label = request.POST.get(f'indicateur_produit_label_{axe_count}_{effet_count}_{produit_count}_{ind_produit_count}')
                                ind_ref = request.POST.get(f'indicateur_produit_reference_{axe_count}_{effet_count}_{produit_count}_{ind_produit_count}', '')
                                if ind_label:
                                    ind_cibles = []
                                    for i in range(horizon):
                                        cible = request.POST.get(f'indicateur_produit_cible_{axe_count}_{effet_count}_{produit_count}_{ind_produit_count}_{i}', '')
                                        ind_cibles.append(cible if cible else "")
                                    IndicateurProduit.objects.create(
                                        produit=produit,
                                        label=ind_label,
                                        reference=ind_ref,
                                        cibles=ind_cibles,
                                    )

                            # Traitement des Actions
                            action_count = 0
                            while f'action_titre_{axe_count}_{effet_count}_{produit_count}_{action_count + 1}' in request.POST:
                                action_count += 1
                                action_titre = request.POST.get(f'action_titre_{axe_count}_{effet_count}_{produit_count}_{action_count}')
                                logger.debug(f"Action {axe_count}.{effet_count}.{produit_count}.{action_count} - titre: {action_titre}")
                                if not action_titre:
                                    raise ValueError(f"Le titre de l'action {axe_count}.{effet_count}.{produit_count}.{action_count} est requis.")
                                
                                action_reference = f"{produit.reference}.{action_count}"
                                action = Action(
                                    produit=produit,
                                    titre=action_titre,
                                    reference=action_reference,
                                )
                                action.save()
                                logger.debug(f"Action {axe_count}.{effet_count}.{produit_count}.{action_count} créé avec ID: {action.id}, reference: {action.reference}")

                                # Traitement des Activités
                                activite_count = 0
                                while f'activite_titre_{axe_count}_{effet_count}_{produit_count}_{action_count}_{activite_count + 1}' in request.POST:
                                    activite_count += 1

                                    activite_titre = request.POST.get(f'activite_titre_{axe_count}_{effet_count}_{produit_count}_{action_count}_{activite_count}')
                                    activite_type = request.POST.get(f'activite_type_{axe_count}_{effet_count}_{produit_count}_{action_count}_{activite_count}')
                                    activite_structure = request.POST.get(f'activite_structure_{axe_count}_{effet_count}_{produit_count}_{action_count}_{activite_count}')
                                    indicateur_label = request.POST.get(f'indicateur_label_{axe_count}_{effet_count}_{produit_count}_{action_count}_{activite_count}')
                                    indicateur_reference = request.POST.get(f'indicateur_reference_{axe_count}_{effet_count}_{produit_count}_{action_count}_{activite_count}')

                                    if not all([activite_titre, activite_type, activite_structure, indicateur_label, indicateur_reference]):
                                        raise ValueError(f"Les champs de l'activité {axe_count}.{effet_count}.{produit_count}.{action_count}.{activite_count} doivent être remplis.")

                                    activite_couts = []
                                    activite_cibles = []
                                    activite_periodes = []
                                    for i in range(horizon):
                                        cout = request.POST.get(f'cout_{axe_count}_{effet_count}_{produit_count}_{action_count}_{activite_count}_{i}', '0')
                                        activite_couts.append(float(cout) if cout else 0.0)
                                        cible = request.POST.get(f'cible_{axe_count}_{effet_count}_{produit_count}_{action_count}_{activite_count}_{i}', '')
                                        activite_cibles.append(cible if cible else "Non définie")
                                        periodes = []
                                        for t in range(1, 5):
                                            periode_key = f'periode_{axe_count}_{effet_count}_{produit_count}_{action_count}_{activite_count}_{i}_T{t}'
                                            if request.POST.get(periode_key):
                                                periodes.append(f'T{t}')
                                        activite_periodes.append(periodes)

                                    activite_reference = f"{action.reference}.{activite_count}"
                                    activite = Activite(
                                        action=action,
                                        titre=activite_titre,
                                        type=activite_type,
                                        structure=activite_structure,
                                        indicateur_label=indicateur_label,
                                        indicateur_reference=indicateur_reference,
                                        point_focal=request.user,
                                        responsable=None,
                                        couts=activite_couts,
                                        cibles=activite_cibles,
                                        periodes_execution=activite_periodes,
                                        reference=activite_reference,
                                    )
                                    activite.save(user=request.user)
                                    logger.debug(f"Activité {axe_count}.{effet_count}.{produit_count}.{action_count}.{activite_count} créée avec ID: {activite.id}")

                messages.success(request, f"Plan d'action '{plan_action.titre}' créé avec succès (Référence: {plan_action.reference}).")
                logger.debug("Plan d'action créé avec succès, redirection vers 'plan_action_list'")
                return redirect('plan_action_list')

        except ValueError as ve:
            logger.error(f"Erreur de validation : {str(ve)}")
            messages.error(request, f"Erreur de validation : {str(ve)}")
            return render(request, 'planning/add_plan_action.html', {'form_data': request.POST})
        except Exception as e:
            logger.error(f"Erreur inattendue : {str(e)}", exc_info=True)
            messages.error(request, f"Erreur lors de la création du plan d'action : {str(e)}")
            return render(request, 'planning/add_plan_action.html', {'form_data': request.POST})
        
    logger.debug("Requête GET : Affichage du formulaire vide")
    return render(request, 'planning/add_plan_action.html', {})

def edit_plan_action(request, id):
    plan_action = get_object_or_404(PlanAction, id=id)
    
    is_authenticated = request.user.is_authenticated
    if not (is_authenticated):
        return render(request, 'planning/access_denied.html')
    
    is_pf_or_se = request.user.role in ['point_focal', 'suiveur_evaluateur']
    if not (is_pf_or_se):
        return render(request, 'planning/access_denied.html')
    
    if request.method == 'POST':
        logger.debug(f"Contenu complet de request.POST : {request.POST}")
        try:
            with transaction.atomic():
                # Mise à jour du PlanAction
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

                # Traitement des Axes existants et nouveaux
                axe_count = 0
                axes_existants = {axe.id: axe for axe in plan_action.plan_axe.all()}
                axes_a_supprimer = set(axes_existants.keys())

                while f'axe_titre_{axe_count + 1}' in request.POST:
                    axe_count += 1
                    axe_titre = request.POST.get(f'axe_titre_{axe_count}')
                    axe_id = request.POST.get(f'axe_id_{axe_count}', None)
                    if not axe_titre:
                        raise ValueError(f"Le titre de l'axe {axe_count} est requis.")

                    if axe_id and int(axe_id) in axes_existants:
                        axe = axes_existants[int(axe_id)]
                        axe.titre = axe_titre
                        axe.save()
                        axes_a_supprimer.discard(int(axe_id))
                    else:
                        axe_reference = str(axe_count)
                        axe = Axe(
                            plan=plan_action,
                            titre=axe_titre,
                            reference=axe_reference,
                        )
                        axe.save()

                    # Traitement des Effets
                    effet_count = 0
                    effets_existants = {effet.id: effet for effet in axe.axe_effet.all()}
                    effets_a_supprimer = set(effets_existants.keys())

                    while f'effet_titre_{axe_count}_{effet_count + 1}' in request.POST:
                        effet_count += 1
                        effet_titre = request.POST.get(f'effet_titre_{axe_count}_{effet_count}')
                        effet_id = request.POST.get(f'effet_id_{axe_count}_{effet_count}', None)
                        if not effet_titre:
                            raise ValueError(f"Le titre de l'effet {axe_count}.{effet_count} est requis.")

                        if effet_id and int(effet_id) in effets_existants:
                            effet = effets_existants[int(effet_id)]
                            effet.titre = effet_titre
                            effet.save()
                            effets_a_supprimer.discard(int(effet_id))
                        else:
                            effet_reference = f"{axe.reference}.{effet_count}"
                            effet = Effet(
                                axe=axe,
                                titre=effet_titre,
                                reference=effet_reference,
                            )
                            effet.save()

                        # Traitement des indicateurs d'effet (supprimer et recréer)
                        effet.indicateurs.all().delete()
                        ind_effet_count = 0
                        while f'indicateur_effet_label_{axe_count}_{effet_count}_{ind_effet_count + 1}' in request.POST:
                            ind_effet_count += 1
                            ind_label = request.POST.get(f'indicateur_effet_label_{axe_count}_{effet_count}_{ind_effet_count}')
                            ind_ref = request.POST.get(f'indicateur_effet_reference_{axe_count}_{effet_count}_{ind_effet_count}', '')
                            if ind_label:
                                ind_cibles = []
                                for i in range(horizon):
                                    cible = request.POST.get(f'indicateur_effet_cible_{axe_count}_{effet_count}_{ind_effet_count}_{i}', '')
                                    ind_cibles.append(cible if cible else "")
                                IndicateurEffet.objects.create(
                                    effet=effet,
                                    label=ind_label,
                                    reference=ind_ref,
                                    cibles=ind_cibles,
                                )

                        # Traitement des Produits
                        produit_count = 0
                        produits_existants = {produit.id: produit for produit in effet.effet_produit.all()}
                        produits_a_supprimer = set(produits_existants.keys())

                        while f'produit_titre_{axe_count}_{effet_count}_{produit_count + 1}' in request.POST:
                            produit_count += 1
                            produit_titre = request.POST.get(f'produit_titre_{axe_count}_{effet_count}_{produit_count}')
                            produit_id = request.POST.get(f'produit_id_{axe_count}_{effet_count}_{produit_count}', None)
                            if not produit_titre:
                                raise ValueError(f"Le titre du produit {axe_count}.{effet_count}.{produit_count} est requis.")

                            if produit_id and int(produit_id) in produits_existants:
                                produit = produits_existants[int(produit_id)]
                                produit.titre = produit_titre
                                produit.save()
                                produits_a_supprimer.discard(int(produit_id))
                            else:
                                produit_reference = f"{effet.reference}.{produit_count}"
                                produit = Produit(
                                    effet=effet,
                                    titre=produit_titre,
                                    reference=produit_reference,
                                )
                                produit.save()

                            # Traitement des indicateurs de produit (supprimer et recréer)
                            produit.indicateurs.all().delete()
                            ind_produit_count = 0
                            while f'indicateur_produit_label_{axe_count}_{effet_count}_{produit_count}_{ind_produit_count + 1}' in request.POST:
                                ind_produit_count += 1
                                ind_label = request.POST.get(f'indicateur_produit_label_{axe_count}_{effet_count}_{produit_count}_{ind_produit_count}')
                                ind_ref = request.POST.get(f'indicateur_produit_reference_{axe_count}_{effet_count}_{produit_count}_{ind_produit_count}', '')
                                if ind_label:
                                    ind_cibles = []
                                    for i in range(horizon):
                                        cible = request.POST.get(f'indicateur_produit_cible_{axe_count}_{effet_count}_{produit_count}_{ind_produit_count}_{i}', '')
                                        ind_cibles.append(cible if cible else "")
                                    IndicateurProduit.objects.create(
                                        produit=produit,
                                        label=ind_label,
                                        reference=ind_ref,
                                        cibles=ind_cibles,
                                    )

                            # Traitement des Actions
                            action_count = 0
                            actions_existantes = {action.id: action for action in produit.produit_action.all()}
                            actions_a_supprimer = set(actions_existantes.keys())

                            while f'action_titre_{axe_count}_{effet_count}_{produit_count}_{action_count + 1}' in request.POST:
                                action_count += 1
                                action_titre = request.POST.get(f'action_titre_{axe_count}_{effet_count}_{produit_count}_{action_count}')
                                action_id = request.POST.get(f'action_id_{axe_count}_{effet_count}_{produit_count}_{action_count}', None)
                                if not action_titre:
                                    raise ValueError(f"Le titre de l'action {axe_count}.{effet_count}.{produit_count}.{action_count} est requis.")

                                if action_id and int(action_id) in actions_existantes:
                                    action = actions_existantes[int(action_id)]
                                    action.titre = action_titre
                                    action.save()
                                    actions_a_supprimer.discard(int(action_id))
                                else:
                                    action_reference = f"{produit.reference}.{action_count}"
                                    action = Action(
                                        produit=produit,
                                        titre=action_titre,
                                        reference=action_reference,
                                    )
                                    action.save()

                                # Traitement des Activités
                                activite_count = 0
                                activites_existantes = {activite.id: activite for activite in action.action_activite.all()}
                                activites_a_supprimer = set(activites_existantes.keys())

                                while f'activite_titre_{axe_count}_{effet_count}_{produit_count}_{action_count}_{activite_count + 1}' in request.POST:
                                    activite_count += 1
                                    activite_titre = request.POST.get(f'activite_titre_{axe_count}_{effet_count}_{produit_count}_{action_count}_{activite_count}')
                                    activite_type = request.POST.get(f'activite_type_{axe_count}_{effet_count}_{produit_count}_{action_count}_{activite_count}')
                                    activite_structure = request.POST.get(f'activite_structure_{axe_count}_{effet_count}_{produit_count}_{action_count}_{activite_count}')
                                    indicateur_label = request.POST.get(f'indicateur_label_{axe_count}_{effet_count}_{produit_count}_{action_count}_{activite_count}')
                                    indicateur_reference = request.POST.get(f'indicateur_reference_{axe_count}_{effet_count}_{produit_count}_{action_count}_{activite_count}')
                                    activite_id = request.POST.get(f'activite_id_{axe_count}_{effet_count}_{produit_count}_{action_count}_{activite_count}', None)

                                    if not all([activite_titre, activite_type, activite_structure, indicateur_label, indicateur_reference]):
                                        raise ValueError(f"Les champs de l'activité {axe_count}.{effet_count}.{produit_count}.{action_count}.{activite_count} doivent être remplis.")

                                    activite_couts = []
                                    activite_cibles = []
                                    activite_periodes = []
                                    for i in range(horizon):
                                        cout = request.POST.get(f'cout_{axe_count}_{effet_count}_{produit_count}_{action_count}_{activite_count}_{i}', '0')
                                        activite_couts.append(float(cout) if cout else 0.0)
                                        cible = request.POST.get(f'cible_{axe_count}_{effet_count}_{produit_count}_{action_count}_{activite_count}_{i}', '')
                                        activite_cibles.append(cible if cible else "Non définie")
                                        periodes = []
                                        for t in range(1, 5):
                                            periode_key = f'periode_{axe_count}_{effet_count}_{produit_count}_{action_count}_{activite_count}_{i}_T{t}'
                                            if request.POST.get(periode_key):
                                                periodes.append(f'T{t}')
                                        activite_periodes.append(periodes)

                                    if activite_id and int(activite_id) in activites_existantes:
                                        activite = activites_existantes[int(activite_id)]
                                        activite.titre = activite_titre
                                        activite.type = activite_type
                                        activite.structure = activite_structure
                                        activite.indicateur_label = indicateur_label
                                        activite.indicateur_reference = indicateur_reference
                                        activite.couts = activite_couts
                                        activite.cibles = activite_cibles
                                        activite.periodes_execution = activite_periodes
                                        activite.save(user=request.user)
                                        activites_a_supprimer.discard(int(activite_id))
                                    else:
                                        activite_reference = f"{action.reference}.{activite_count}"
                                        activite = Activite(
                                            action=action,
                                            titre=activite_titre,
                                            type=activite_type,
                                            structure=activite_structure,
                                            indicateur_label=indicateur_label,
                                            indicateur_reference=indicateur_reference,
                                            point_focal=request.user,
                                            responsable=None,
                                            couts=activite_couts,
                                            cibles=activite_cibles,
                                            periodes_execution=activite_periodes,
                                            reference=activite_reference,
                                        )
                                        activite.save(user=request.user)

                                # Supprimer les activités non présentes dans le formulaire
                                for activite_id in activites_a_supprimer:
                                    activites_existantes[activite_id].delete()

                            # Supprimer les actions non présentes dans le formulaire
                            for action_id in actions_a_supprimer:
                                actions_existantes[action_id].delete()

                        # Supprimer les produits non présents dans le formulaire
                        for produit_id in produits_a_supprimer:
                            produits_existants[produit_id].delete()

                    # Supprimer les effets non présents dans le formulaire
                    for effet_id in effets_a_supprimer:
                        effets_existants[effet_id].delete()

                # Supprimer les axes non présents dans le formulaire
                for axe_id in axes_a_supprimer:
                    axes_existants[axe_id].delete()

                messages.success(request, f"Plan d'action '{plan_action.titre}' modifié avec succès (Référence: {plan_action.reference}).")
                logger.debug("Plan d'action modifié avec succès, redirection vers 'plan_action_list'")
                return redirect('plan_action_list')

        except ValueError as ve:
            logger.error(f"Erreur de validation : {str(ve)}")
            messages.error(request, f"Erreur de validation : {str(ve)}")
            return render(request, 'planning/edit_plan_action.html', {'plan_action': plan_action, 'form_data': request.POST})
        except Exception as e:
            logger.error(f"Erreur inattendue : {str(e)}", exc_info=True)
            messages.error(request, f"Erreur lors de la modification du plan d'action : {str(e)}")
            return render(request, 'planning/edit_plan_action.html', {'plan_action': plan_action, 'form_data': request.POST})

    logger.debug("Requête GET : Affichage du formulaire avec données existantes")
    return render(request, 'planning/edit_plan_action.html', {'plan_action': plan_action})

def pppbse_gar(request):
    return render(request, 'planning/pppbse_gar.html')

## Plan d'Actions
def plan_action_list(request):
    
    is_authenticated = request.user.is_authenticated
    if not (is_authenticated):
        return render(request, 'planning/access_denied.html')
    
    is_pf_or_resp_or_se_or_cab = request.user.role in ['point_focal', 'responsable', 'suiveur_evaluateur', 'cabinet']
    if not (is_pf_or_resp_or_se_or_cab):
        return render(request, 'planning/access_denied.html')

    plans = PlanAction.objects.all()
    context = {
        'plans': plans,
    }
    return render(request, 'planning/plan_action_list.html', context)

def plan_action_detail(request, id):
    plan = get_object_or_404(PlanAction, id=id)

    # Données initiales pour le rendu du template
    axe_list = Axe.objects.filter(plan=plan)
    effets = Effet.objects.filter(axe__plan=plan)
    produits = Produit.objects.filter(effet__axe__plan=plan).select_related('effet')
    actions = Action.objects.filter(produit__effet__axe__plan=plan).select_related('produit__effet')
    activites = Activite.objects.filter(action__produit__effet__axe__plan=plan).select_related('action__produit__effet', 'point_focal')
    types = list(set(activite.type or "N/A" for activite in activites))
    structures = list(set(activite.point_focal.entity if activite.point_focal and hasattr(activite.point_focal, 'entity') else "N/A" for activite in activites))
    annees = [str(plan.annee_debut + i) for i in range(plan.horizon)] if plan.annee_debut and plan.horizon else []

    def calculate_total_cost(couts):
        if not couts or not isinstance(couts, (list, tuple)):
            return "N/A"
        total = sum(float(cout) for cout in couts if isinstance(cout, (int, float, str)) and str(cout).replace('.', '', 1).isdigit())
        return "{:.2f}".format(total)

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
                            'total_cost': calculate_total_cost(action.couts),
                            'activites': [
                                {
                                    'id': activite.id,
                                    'titre': activite.titre,
                                    'type': activite.type or 'N/A',
                                    'couts': activite.couts,
                                    'total_cost': calculate_total_cost(activite.couts),
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
                        'total_cost': calculate_total_cost(produit.couts),
                        'actions': actions_data,
                        'indicateurs': [
                            {'label': ind.label, 'reference': ind.reference, 'cibles': ind.cibles}
                            for ind in produit.indicateurs.all()
                        ]
                    })
                effets_data.append({
                    'id': effet.id,
                    'titre': effet.titre,
                    'couts': effet.couts,
                    'total_cost': calculate_total_cost(effet.couts),
                    'produits': produits_data,
                    'indicateurs': [
                        {'label': ind.label, 'reference': ind.reference, 'cibles': ind.cibles}
                        for ind in effet.indicateurs.all()
                    ]
                })

            # Calcul du coût total global
            total_couts = []
            for effet in filtered_effets:
                for cout in effet.couts or []:
                    total_couts.append(cout)
                for produit in produits.filter(effet=effet):
                    for cout in produit.couts or []:
                        total_couts.append(cout)
                    for action in actions.filter(produit=produit):
                        for cout in action.couts or []:
                            total_couts.append(cout)
                        for activite in activites.filter(action=action):
                            for cout in activite.couts or []:
                                total_couts.append(cout)

            # Mettre à jour les filtres dépendants
            types = list(set(activite.type or 'N/A' for activite in activites))
            structures = list(set(activite.point_focal.entity if activite.point_focal and hasattr(activite.point_focal, 'entity') else 'N/A' for activite in activites))

            data = {
                'effets': effets_data,
                'produits': [{'id': p.id, 'titre': p.titre, 'couts': p.couts, 'total_cost': calculate_total_cost(p.couts)} for p in produits],
                'actions': [{'id': a.id, 'titre': a.titre, 'couts': a.couts, 'total_cost': calculate_total_cost(a.couts)} for a in actions],
                'activites': [
                    {
                        'id': a.id,
                        'titre': a.titre,
                        'type': a.type or 'N/A',
                        'couts': a.couts,
                        'total_cost': calculate_total_cost(a.couts),
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
                'annee_debut': plan.annee_debut,
                'total_cost_global': calculate_total_cost(total_couts)
            }

            return JsonResponse(data, safe=False)

        except Exception as e:
            print(f"🚨 Erreur lors du filtrage: {str(e)}")
            return JsonResponse({"error": "Erreur interne", "details": str(e)}, status=500)

    return render(request, 'planning/plan_action_detail.html', {
        "plan": plan,
        "axes": axe_list,
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
    
    entity = getattr(request.user, 'entity', None)
    
    # Passer 'entity' au contexte du template
    return render(request, 'planning/pao_list.html', {
        'plan': plan,
        'paos': paos,
        'entity': entity
    })

@login_required(login_url='connexion_membre')
def manage_activities(request, plan_id, entity):
    plan = get_object_or_404(PlanAction, id=plan_id)
    
    annee = int(request.GET.get('annee', plan.annee_debut))
    index = annee - plan.annee_debut
    if index < 0 or index >= plan.horizon:
        messages.error(request, "Année invalide.")
        return render(request, 'planning/access_denied.html', {'message': "Année invalide."})

    filters = Q(action__produit__effet__axe__plan=plan)
    filters &= Q(point_focal__entity=request.user.entity)
    
    activites = Activite.objects.filter(filters).distinct()

    is_responsable = any(a.responsable == request.user for a in activites)
    is_point_focal = any(a.point_focal == request.user for a in activites)

    if not (is_responsable or is_point_focal):
        messages.error(request, "Vous n'avez pas les permissions nécessaires pour gérer ces activités.")
        return render(request, 'planning/access_denied.html', {'message': "Accès non autorisé."})

    has_no_responsable = is_point_focal and any(a.responsable is None for a in activites)

    if request.method == 'POST':
        data = request.POST
        activite = get_object_or_404(Activite, id=data.get('activite_id'))

        activite_entity = getattr(activite.point_focal, 'entity', None)
        if activite_entity != request.user.entity:
            return JsonResponse({'success': False, 'message': "Activité hors de votre structure."})

        horizon = plan.horizon
        for attr in ['realisation', 'etat_avancement', 'commentaire', 'commentaire_se', 'status', 'matrix_status', 'pending_changes', 'proposed_changes']:
            if not getattr(activite, attr) or len(getattr(activite, attr)) < horizon:
                setattr(activite, attr, [''] * horizon if attr in ['realisation', 'etat_avancement', 'commentaire', 'commentaire_se'] else ['Non évaluée'] * horizon if attr == 'status' else ['En cours'] * horizon if attr == 'matrix_status' else [{}] * horizon)

        new_data = {
            'etat_avancement': data.get('etat_avancement', ''),
            'realisation': data.get('realisation', ''),
            'commentaire': data.get('commentaire', ''),
        }

        if 'submit' in data and is_responsable:
            activite.propose_changes(
                user=request.user,
                index=index,
                etat_avancement=new_data['etat_avancement'],
                realisation=new_data['realisation'],
                commentaire=new_data['commentaire']
            )
            changes = {k: {'avant': activite.pending_changes[index].get(k, ''), 'apres': new_data[k]} for k in new_data if activite.pending_changes[index].get(k, '') != new_data[k]}
            if changes:
                ActiviteLog.objects.create(
                    activite=activite,
                    user=request.user,
                    modifications={'year_index': index, 'changes': changes},
                    statut_apres=activite.status[index]
                )
            return JsonResponse({'success': True, 'message': 'Modifications soumises à l’évaluation'})
        
        elif 'propose' in data and is_point_focal:
            activite.propose_changes(
                user=request.user,
                index=index,
                etat_avancement=new_data['etat_avancement'],
                realisation=new_data['realisation'],
                commentaire=new_data['commentaire']
            )
            return JsonResponse({'success': True, 'message': 'Proposition enregistrée pour validation par le responsable'})

    activites_list = []
    for a in activites:
        horizon = plan.horizon
        for attr in ['realisation', 'etat_avancement', 'commentaire', 'commentaire_se', 'status', 'matrix_status', 'couts', 'cibles', 'pending_changes', 'proposed_changes', 'periodes_execution']:
            if not getattr(a, attr) or len(getattr(a, attr)) != horizon:
                setattr(a, attr, [''] * horizon if attr in ['realisation', 'etat_avancement', 'commentaire', 'commentaire_se'] else ['Non évaluée'] * horizon if attr == 'status' else ['En cours'] * horizon if attr == 'matrix_status' else [0.0] * horizon if attr == 'cibles' else [{}] * horizon if attr in ['pending_changes', 'proposed_changes'] else [''] * horizon)
                a.save()

        model_values = {
            'realisation': a.realisation[index],
            'etat_avancement': a.etat_avancement[index],
            'commentaire': a.commentaire[index],
            'commentaire_se': a.commentaire_se[index],
            'status': a.status[index],
            'matrix_status': a.matrix_status[index],
        }
        
        pending = a.pending_changes[index] if a.pending_changes and len(a.pending_changes) > index else {}
        proposed = a.proposed_changes[index] if a.proposed_changes and len(a.proposed_changes) > index else {}

        # Prioriser proposed_changes pour PF et Resp si existant, sinon pending_changes
        latest_changes = proposed if proposed.get('last_modified_by', '') and (is_point_focal or is_responsable) else pending

        pf_values = {
            'realisation': latest_changes.get('realisation', model_values['realisation']),
            'etat_avancement': latest_changes.get('etat_avancement', model_values['etat_avancement']),
            'commentaire': latest_changes.get('commentaire', model_values['commentaire']),
        }
        resp_values = {
            'realisation': latest_changes.get('realisation', model_values['realisation']),
            'etat_avancement': latest_changes.get('etat_avancement', model_values['etat_avancement']),
            'commentaire': latest_changes.get('commentaire', model_values['commentaire']),
        }

        try:
            periodes = a.periodes_execution[index] if a.periodes_execution and len(a.periodes_execution) > index else ''
            trimestres_suivi = [
                'T1' in periodes,
                'T2' in periodes,
                'T3' in periodes,
                'T4' in periodes
            ]
        except (TypeError, IndexError):
            trimestres_suivi = [False, False, False, False]

        last_modified_by = latest_changes.get('last_modified_by', '')
        last_is_responsable = False
        if last_modified_by:
            last_user = User.objects.filter(username=last_modified_by).first()
            if last_user:
                last_is_responsable = (last_user == a.responsable)

        activites_list.append({
            'id': a.id,
            'reference': a.reference or '',
            'titre': a.titre,
            'type': a.type,
            'indicateur_label': a.indicateur_label,
            'indicateur_reference': a.indicateur_reference,
            'model_etat_avancement': model_values['etat_avancement'],
            'model_realisation': model_values['realisation'],
            'model_commentaire': model_values['commentaire'],
            'model_commentaire_se': model_values['commentaire_se'],
            'model_status': model_values['status'],
            'model_matrix_status': model_values['matrix_status'],
            'pf_etat_avancement': pf_values['etat_avancement'],
            'pf_realisation': pf_values['realisation'],
            'pf_commentaire': pf_values['commentaire'],
            'resp_etat_avancement': resp_values['etat_avancement'],
            'resp_realisation': resp_values['realisation'],
            'resp_commentaire': resp_values['commentaire'],
            'cout': a.couts[index],
            'cible': a.cibles[index],
            'pending_changes': a.pending_changes[index],
            'proposed_changes': a.proposed_changes[index],
            'pending_status' : a.pending_changes[index].get('status', '') if a.pending_changes and len(a.pending_changes) > index else '',  
            'pending_commentaire_se' : a.pending_changes[index].get('commentaire_se', '') if a.pending_changes and len(a.pending_changes) > index else '',
            'pending_matrix_status' : a.pending_changes[index].get('matrix_status', '') if a.pending_changes and len(a.pending_changes) > index else '',
            'is_submitted': bool(a.pending_changes[index]),
            'trimestres_suivi': trimestres_suivi,
            'last_modified_by': last_modified_by,
            'last_is_responsable': last_is_responsable,
            'has_responsable': a.responsable is not None,
        })

    context = {
        'plan': plan,
        'annee': annee,
        'entity': entity,
        'activites': activites_list,
        'is_responsable': is_responsable,
        'is_point_focal': is_point_focal,
        'has_no_responsable': has_no_responsable,
    }
    return render(request, 'planning/manage_activities.html', context)

@login_required(login_url='connexion_membre')
def track_execution_list(request, plan_id):
    plan = get_object_or_404(PlanAction, id=plan_id)
    is_se = request.user.groups.filter(name='SuiveurEvaluateur').exists()

    # Vérification des permissions
    if not is_se:
        messages.error(request, "Seul un Suiveur-Évaluateur peut accéder à cette page.")
        return render(request, 'planning/access_denied.html', {'plan': plan})

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

@login_required(login_url='connexion_membre')
def track_execution_detail(request, plan_id):
    plan = get_object_or_404(PlanAction, id=plan_id)
    
    # Vérification initiale : seul un SE peut accéder
    is_se = request.user.role in ['suiveur_evaluateur']
    if not is_se:
        return render(request, 'planning/access_denied.html', {'plan': plan})

    annee = request.GET.get('annee')
    if not annee or not annee.isdigit() or int(annee) < plan.annee_debut or int(annee) >= plan.annee_debut + plan.horizon:
        messages.error(request, "Année invalide pour ce plan.")
        return render(request, 'planning/access_denied.html', {
            'message': "Année invalide pour ce plan.",
            'plan': plan
        })

    annee = int(annee)
    index = annee - plan.annee_debut

    pao_statut = plan.statut_pao[index]
    activites = Activite.objects.filter(
        action__produit__effet__axe__plan=plan
    ).select_related('responsable', 'point_focal', 'action__produit__effet')

    # Filtrer les activités
    modified_activite_ids = []
    for activite in activites:
        if len(activite.pending_changes) <= index or not activite.pending_changes[index]:
            continue

        pending = activite.pending_changes[index]
        last_modified_by = pending.get('last_modified_by', '')

        # Ne pas afficher si l'utilisateur actuel (SE) est le dernier modificateur
        if last_modified_by == request.user.username:
            continue

        modified_activite_ids.append(activite.id)

    has_submitted_activities = bool(modified_activite_ids)
    form = PaoStatusForm(initial={'statut': pao_statut})

    if request.method == 'POST':
        data = request.POST

        if 'update_pao_status' in data:
            plan.statut_pao[index] = data.get('statut')
            plan.save()
            messages.success(request, f"Statut du PAO {annee} mis à jour : {data.get('statut')}")
            return render(request, 'planning/track_execution_detail.html', {
                'plan': plan,
                'annee': annee,
                'pao_statut': plan.statut_pao[index],
                'form': PaoStatusForm(initial={'statut': plan.statut_pao[index]}),
                'activites_by_entity': {},
                'is_se': is_se,
            })

        elif 'submit' in data:
            activite = get_object_or_404(Activite, id=data.get('activite_id'))
            horizon = plan.horizon
            for attr in ['status', 'commentaire_se', 'pending_changes']:
                if not getattr(activite, attr) or len(getattr(activite, attr)) < horizon:
                    setattr(activite, attr, ['Non entamée'] * horizon if attr == 'status' else [''] * horizon if attr == 'commentaire_se' else [{}] * horizon)
            
            current_status = data.get('status')
            current_commentaire_se = data.get('commentaire_se')
            pending = activite.pending_changes[index] if activite.pending_changes and len(activite.pending_changes) > index else {}

            valid_statuses = ['Non entamée', 'En cours', 'Réalisée', 'Non réalisée', 'Supprimée', 'Reprogrammée']
            if current_status not in valid_statuses:
                return JsonResponse({
                    'success': False,
                    'message': f"Statut '{current_status}' invalide. Statuts valides : {', '.join(valid_statuses)}"
                })

            matches_pending = (
                pending.get('status', activite.status[index]) == current_status and
                pending.get('commentaire_se', activite.commentaire_se[index]) == current_commentaire_se
            )

            response_data = {
                'success': True,
                'model_status': activite.status[index],
                'model_commentaire_se': activite.commentaire_se[index],
                'pending_status': pending.get('status', ''),
                'pending_commentaire_se': pending.get('commentaire_se', ''),
                'last_modified_by': pending.get('last_modified_by', ''),
            }

            if matches_pending:
                # "Soumettre" : Appliquer au modèle
                activite.apply_pending_changes(request.user, index)
                response_data.update({
                    'message': 'Modifications appliquées au modèle réel',
                    'action': 'model',
                    'model_status': activite.status[index],
                    'model_commentaire_se': activite.commentaire_se[index],
                    'pending_status': '',
                    'pending_commentaire_se': '',
                    'last_modified_by': '',
                })
            else:
                # "Renvoyer" : Mettre à jour pending_changes
                activite.propose_changes(
                    user=request.user,
                    index=index,
                    status=current_status,
                    commentaire_se=current_commentaire_se
                )
                response_data.update({
                    'message': 'Propositions renvoyées au point focal et son responsable',
                    'action': 'pending',
                    'pending_status': current_status,
                    'pending_commentaire_se': current_commentaire_se,
                    'last_modified_by': request.user.username,
                })

            return JsonResponse(response_data)

    activites_by_entity = {}
    for a in activites.filter(id__in=modified_activite_ids):
        horizon = plan.horizon
        for attr in ['realisation', 'etat_avancement', 'commentaire', 'commentaire_se', 'status', 'couts', 'cibles', 'pending_changes']:
            if not getattr(a, attr) or len(getattr(a, attr)) != horizon:
                setattr(a, attr, [''] * horizon if attr in ['realisation', 'etat_avancement', 'commentaire', 'commentaire_se'] else ['Non entamée'] * horizon if attr == 'status' else [0.0] * horizon if attr == 'couts' else [None] * horizon if attr == 'cibles' else [{}] * horizon)
                a.save()

        pending = a.pending_changes[index] if a.pending_changes and len(a.pending_changes) > index else {}
        display_values = {
            'realisation': pending.get('realisation', a.realisation[index]) if pending else a.realisation[index],
            'etat_avancement': pending.get('etat_avancement', a.etat_avancement[index]) if pending else a.etat_avancement[index],
            'commentaire': pending.get('commentaire', a.commentaire[index]) if pending else a.commentaire[index],
            'commentaire_se': pending.get('commentaire_se', a.commentaire_se[index]) if pending else a.commentaire_se[index],
            'status': pending.get('status', a.status[index]) if pending else a.status[index],
        }

        try:
            periodes = a.periodes_execution[index]
            trimestres_suivi = ['T1' in periodes, 'T2' in periodes, 'T3' in periodes, 'T4' in periodes]
        except (TypeError, IndexError):
            trimestres_suivi = [False, False, False, False]

        entity = (a.point_focal.entity if a.point_focal and hasattr(a.point_focal, 'entity') else 
                  a.responsable.entity if a.responsable and hasattr(a.responsable, 'entity') else 'Sans entité')
        if entity not in activites_by_entity:
            activites_by_entity[entity] = []
        
        last_modified_by = pending.get('last_modified_by', '') if pending else ''

        activites_by_entity[entity].append({
            'id': a.id,
            'reference': a.reference or '',
            'titre': a.titre,
            'type': a.type,
            'indicateur_label': a.indicateur_label,
            'indicateur_reference': a.indicateur_reference,
            'etat_avancement': display_values['etat_avancement'],
            'realisation': display_values['realisation'],
            'cout': a.couts[index],
            'cible': a.cibles[index],
            'commentaire': display_values['commentaire'],
            'commentaire_se': display_values['commentaire_se'],
            'status': display_values['status'],
            'pending_changes': a.pending_changes[index],
            'trimestres_suivi': trimestres_suivi,
            'pending_commentaire_se': pending.get('commentaire_se', '') if pending else '',
            'pending_status': pending.get('status', '') if pending else '',
            'model_status': a.status[index],
            'model_commentaire_se': a.commentaire_se[index],
            'last_modified_by': last_modified_by,
        })

    context = {
        'plan': plan,
        'annee': annee,
        'pao_statut': pao_statut,
        'form': form,
        'activites_by_entity': activites_by_entity,
        'is_se': is_se,
        'current_user': request.user.username,
    }
    return render(request, 'planning/track_execution_detail.html', context)

def operational_plan_matrix(request, plan_id, annee):
    # Récupérer le plan
    plan = get_object_or_404(PlanAction, id=plan_id)
    annees = [plan.annee_debut + i for i in range(plan.horizon)]
    if annee not in annees:
        annee = annees[0]
    annee_index = annees.index(annee)

    # Pré-chargement optimisé des relations avec prefetch_related
    effets = Effet.objects.filter(axe__plan=plan).prefetch_related(
        'indicateurs',
        'effet_produit__indicateurs',
        'effet_produit__produit_action__action_activite__point_focal',
        'effet_produit__produit_action__action_activite__responsable'
    )
    effets_data = []

    for effet in effets:
        produits_data = []
        for produit in effet.effet_produit.all():
            actions_data = []
            for action in produit.produit_action.all():
                activites_data = []
                for activite in action.action_activite.all():
                    horizon = plan.horizon
                    # Initialisation des champs JSONField avec vérification d'intégrité
                    for field, default in [
                        ('realisation', ''),
                        ('couts', 0.0),
                        ('cibles', None),
                        ('etat_avancement', ''),
                        ('commentaire', ''),
                        ('commentaire_se', ''),
                        ('status', 'Non entamée'),
                        ('matrix_status', 'en cours')
                    ]:
                        current = getattr(activite, field)
                        if not current or len(current) != horizon:
                            setattr(activite, field, [default] * horizon)
                            activite.save()

                    activites_data.append({
                        'id': activite.id,
                        'titre': activite.titre,
                        'type': activite.type or 'N/A',
                        'indicateur_label': activite.indicateur_label or 'N/A',
                        'indicateur_reference': activite.indicateur_reference or 'N/A',
                        'cible': activite.cibles[annee_index],
                        'structure': (
                            activite.point_focal.entity if activite.point_focal and hasattr(activite.point_focal, 'entity') else 
                            activite.responsable.entity if activite.responsable and hasattr(activite.responsable, 'entity') else 'Sans entité'
                        ),
                        'cout': float(activite.couts[annee_index]),
                        'realisation': activite.realisation[annee_index],
                        'etat_avancement': activite.etat_avancement[annee_index],
                        'commentaire': activite.commentaire[annee_index],
                        'commentaire_se': activite.commentaire_se[annee_index],
                        'status': activite.status[annee_index],
                        'matrix_status': activite.matrix_status[annee_index],
                        'programme': activite.point_focal.program,
                    })
                if activites_data:
                    actions_data.append({
                        'titre': action.titre,
                        'cout': sum(a['cout'] for a in activites_data),
                        'activites': activites_data,
                    })
            if actions_data:
                produits_data.append({
                    'titre': produit.titre,
                    'cout': sum(a['cout'] for a in actions_data),
                    'actions': actions_data,
                    'indicateurs': [
                        {'label': ind.label, 'reference': ind.reference, 'cible': ind.cibles[annee_index] if ind.cibles and len(ind.cibles) > annee_index else ''}
                        for ind in produit.indicateurs.all()
                    ],
                })
        if produits_data:
            effets_data.append({
                'titre': effet.titre,
                'cout': sum(p['cout'] for p in produits_data),
                'produits': produits_data,
                'indicateurs': [
                    {'label': ind.label, 'reference': ind.reference, 'cible': ind.cibles[annee_index] if ind.cibles and len(ind.cibles) > annee_index else ''}
                    for ind in effet.indicateurs.all()
                ],
            })

    # Options de filtre (optimisées pour éviter les doublons)
    produits = Produit.objects.filter(effet__axe__plan=plan).distinct()
    actions = Action.objects.filter(produit__effet__axe__plan=plan).distinct()
    types = Activite.objects.filter(action__produit__effet__axe__plan=plan).values_list('type', flat=True).distinct()
    structures = Activite.objects.filter(action__produit__effet__axe__plan=plan).values_list(
        'point_focal__entity', 'responsable__entity'
    ).distinct().exclude(point_focal__entity__isnull=True, responsable__entity__isnull=True)

    # Réponse AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'impact': plan.impact or 'Impact non défini',
            'effets': effets_data,
            'annees': annees,
            'annee': annee,
            'plan_titre': plan.titre,
        })

    # Contexte pour le rendu initial
    context = {
        'plan': plan,
        'impact': plan.impact or 'Impact non défini',
        'effets': effets_data,
        'effet_list': [{'id': e.id, 'titre': e.titre} for e in effets],
        'produit_list': [{'id': p.id, 'titre': p.titre} for p in produits],
        'action_list': [{'id': a.id, 'titre': a.titre} for a in actions],
        'types': list(types.exclude(type__isnull=True)),
        'structures': list(set(s[0] or s[1] for s in structures if s[0] or s[1])),
        'annees': annees,
        'annee': annee,
    }
    filter_groups = [
        {'group': 'effet', 'label': 'Filtrer par effet', 'items': context['effet_list'], 'col_width': 4},
        {'group': 'produit', 'label': 'Filtrer par produit', 'items': context['produit_list'], 'col_width': 4},
        {'group': 'action', 'label': 'Filtrer par action', 'items': context['action_list'], 'col_width': 4},
        {'group': 'type', 'label': 'Filtrer par type', 'items': [{'id': t, 'titre': t} for t in context['types']], 'col_width': 3},
        {'group': 'structure', 'label': 'Filtrer par structure', 'items': [{'id': s, 'titre': s} for s in context['structures']], 'col_width': 3},
    ]
    context['filter_groups'] = filter_groups
    
    return render(request, 'planning/operational_plan_matrix.html', context)

@login_required
def rapport_word(request, plan_id, annee):
    """Génère un rapport Word avec les activités réalisées et en cours, classées par axe/effet/produit."""
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor
    from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
    from docx.enum.table import WD_TABLE_ALIGNMENT
    import io
    from datetime import datetime

    plan = get_object_or_404(PlanAction, id=plan_id)
    annees = [plan.annee_debut + i for i in range(plan.horizon)]
    if annee not in annees:
        annee = annees[0]
    annee_index = annees.index(annee)

    # Récupérer toutes les activités de ce plan pour cette année
    axes = Axe.objects.filter(plan=plan).prefetch_related(
        'axe_effet__effet_produit__produit_action__action_activite__point_focal',
        'axe_effet__effet_produit__produit_action__action_activite__responsable',
    )

    # Construire la hiérarchie avec les activités classées par statut
    def build_hierarchy(status_filter):
        """Construit la hiérarchie axe/effet/produit pour un filtre de statut donné."""
        result = []
        for axe in axes:
            axe_data = {'titre': axe.titre, 'reference': axe.reference, 'effets': []}
            for effet in axe.axe_effet.all():
                effet_data = {'titre': effet.titre, 'reference': effet.reference, 'produits': []}
                for produit in effet.effet_produit.all():
                    produit_data = {'titre': produit.titre, 'reference': produit.reference, 'activites': []}
                    for action in produit.produit_action.all():
                        for activite in action.action_activite.all():
                            # Vérifier que le statut existe pour cette année
                            if activite.status and len(activite.status) > annee_index:
                                if activite.status[annee_index] in status_filter:
                                    realisation = ''
                                    if activite.realisation and len(activite.realisation) > annee_index:
                                        realisation = activite.realisation[annee_index]
                                    etat = ''
                                    if activite.etat_avancement and len(activite.etat_avancement) > annee_index:
                                        etat = activite.etat_avancement[annee_index]
                                    structure = 'N/A'
                                    if activite.point_focal and hasattr(activite.point_focal, 'entity'):
                                        structure = activite.point_focal.entity or 'N/A'
                                    produit_data['activites'].append({
                                        'titre': activite.titre,
                                        'reference': activite.reference,
                                        'indicateur_label': activite.indicateur_label or '',
                                        'realisation': realisation,
                                        'etat_avancement': etat,
                                        'structure': structure,
                                        'status': activite.status[annee_index],
                                    })
                    if produit_data['activites']:
                        effet_data['produits'].append(produit_data)
                if effet_data['produits']:
                    axe_data['effets'].append(effet_data)
            if axe_data['effets']:
                result.append(axe_data)
        return result

    realisees = build_hierarchy(['Réalisée'])
    en_cours = build_hierarchy(['En cours'])

    # Créer le document Word
    doc = Document()

    # Styles
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)

    # Page de titre
    title_para = doc.add_paragraph()
    title_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    title_run = title_para.add_run(f'RAPPORT DE SUIVI-ÉVALUATION')
    title_run.bold = True
    title_run.font.size = Pt(18)
    title_run.font.color.rgb = RGBColor(0, 0, 139)

    subtitle_para = doc.add_paragraph()
    subtitle_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    sub_run = subtitle_para.add_run(f'{plan.titre}')
    sub_run.bold = True
    sub_run.font.size = Pt(14)

    info_para = doc.add_paragraph()
    info_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    info_run = info_para.add_run(f'Année {annee} — Rapport généré le {datetime.now().strftime("%d/%m/%Y à %H:%M")}')
    info_run.font.size = Pt(11)
    info_run.font.color.rgb = RGBColor(100, 100, 100)

    doc.add_paragraph()  # Espace

    def add_section(doc, titre_section, data, color):
        """Ajoute une section (réalisées ou en cours) au document."""
        heading = doc.add_heading(titre_section, level=1)
        for run in heading.runs:
            run.font.color.rgb = color

        if not data:
            p = doc.add_paragraph('Aucune activité dans cette catégorie pour cette période.')
            p.runs[0].font.italic = True
            return

        for axe in data:
            # Titre de l'axe
            axe_heading = doc.add_heading(f'Axe {axe["reference"]} : {axe["titre"]}', level=2)
            for run in axe_heading.runs:
                run.font.color.rgb = RGBColor(51, 51, 51)

            for effet in axe['effets']:
                # Titre de l'effet
                effet_heading = doc.add_heading(f'Effet {effet["reference"]} : {effet["titre"]}', level=3)
                for run in effet_heading.runs:
                    run.font.color.rgb = RGBColor(80, 80, 80)

                for produit in effet['produits']:
                    # Titre du produit
                    produit_para = doc.add_paragraph()
                    produit_run = produit_para.add_run(f'Produit {produit["reference"]} : {produit["titre"]}')
                    produit_run.bold = True
                    produit_run.font.size = Pt(11)

                    # Tableau des activités
                    table = doc.add_table(rows=1, cols=5)
                    table.style = 'Table Grid'
                    table.alignment = WD_TABLE_ALIGNMENT.CENTER

                    # En-tête
                    hdr = table.rows[0]
                    headers = ['Réf.', 'Activité', 'Indicateur', 'Réalisation', 'Structure']
                    for i, h in enumerate(headers):
                        cell = hdr.cells[i]
                        cell.text = h
                        for paragraph in cell.paragraphs:
                            for run in paragraph.runs:
                                run.bold = True
                                run.font.size = Pt(9)

                    # Lignes d'activités
                    for act in produit['activites']:
                        row = table.add_row()
                        row.cells[0].text = str(act.get('reference', ''))
                        row.cells[1].text = act['titre']
                        row.cells[2].text = act.get('indicateur_label', '')
                        row.cells[3].text = str(act.get('realisation', ''))
                        row.cells[4].text = act.get('structure', 'N/A')
                        for cell in row.cells:
                            for paragraph in cell.paragraphs:
                                for run in paragraph.runs:
                                    run.font.size = Pt(9)

                    doc.add_paragraph()  # Espace après le tableau

    # Section 1 : Activités réalisées
    add_section(doc, 'I. ACTIVITÉS RÉALISÉES', realisees, RGBColor(0, 128, 0))

    # Section 2 : Activités en cours de réalisation
    add_section(doc, 'II. ACTIVITÉS EN COURS DE RÉALISATION', en_cours, RGBColor(0, 0, 200))

    # Générer le fichier
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    filename = f'Rapport_SE_{plan.titre[:30]}_{annee}.docx'.replace(' ', '_')
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def performance_matrix(request, plan_id, annee):
    """Matrice de cadre de performance : Axes, Effets et Produits avec leurs indicateurs."""
    plan = get_object_or_404(PlanAction, id=plan_id)
    annees = [plan.annee_debut + i for i in range(plan.horizon)]
    if annee not in annees:
        annee = annees[0]
    annee_index = annees.index(annee)

    # Construire la hiérarchie Axe → Effet → Produit avec indicateurs
    axes = Axe.objects.filter(plan=plan).prefetch_related(
        'axe_effet__indicateurs',
        'axe_effet__effet_produit__indicateurs'
    )

    axes_data = []
    for axe in axes:
        effets_data = []
        for effet in axe.axe_effet.all():
            indicateurs_effet = []
            for ind in effet.indicateurs.all():
                cible_val = ind.cibles[annee_index] if ind.cibles and len(ind.cibles) > annee_index else ''
                indicateurs_effet.append({
                    'label': ind.label,
                    'reference': ind.reference,
                    'cible': cible_val,
                    'cibles': ind.cibles,
                })

            produits_data = []
            for produit in effet.effet_produit.all():
                indicateurs_produit = []
                for ind in produit.indicateurs.all():
                    cible_val = ind.cibles[annee_index] if ind.cibles and len(ind.cibles) > annee_index else ''
                    indicateurs_produit.append({
                        'label': ind.label,
                        'reference': ind.reference,
                        'cible': cible_val,
                        'cibles': ind.cibles,
                    })
                produits_data.append({
                    'titre': produit.titre,
                    'reference': produit.reference,
                    'indicateurs': indicateurs_produit,
                })

            effets_data.append({
                'titre': effet.titre,
                'reference': effet.reference,
                'indicateurs': indicateurs_effet,
                'produits': produits_data,
            })

        axes_data.append({
            'titre': axe.titre,
            'reference': axe.reference,
            'effets': effets_data,
        })

    context = {
        'plan': plan,
        'axes': axes_data,
        'annees': annees,
        'annee': annee,
        'annee_index': annee_index,
    }
    return render(request, 'planning/performance_matrix.html', context)


def hierarchy_review(request, plan_id):
    # Récupérer le PlanAction
    plan = get_object_or_404(PlanAction, id=plan_id)
    
    # Vérifier si l'utilisateur a le rôle hiérarchique
    is_hierarchy = request.user.groups.filter(name='Hierarchy').exists()
    if not is_hierarchy:
        return render(request, 'planning/access_denied.html', {'plan': plan})

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


<<<<<<< HEAD
@login_required
def preuves_activite(request, activite_id):
    """Affiche les preuves d'une activité et permet d'en ajouter."""
    activite = get_object_or_404(Activite, id=activite_id)
    preuves = activite.preuves.all()
    form = PreuveRealisationForm()

    if request.method == 'POST':
        form = PreuveRealisationForm(request.POST, request.FILES)
        if form.is_valid():
            preuve = form.save(commit=False)
            preuve.activite = activite
            preuve.uploaded_by = request.user
            preuve.save()
            messages.success(request, 'Preuve ajoutée avec succès.')
            return redirect('preuves_activite', activite_id=activite.id)

    context = {
        'activite': activite,
        'preuves': preuves,
        'form': form,
        'title': f"Preuves - {activite.reference}",
    }
    return render(request, 'planning/preuves_activite.html', context)


@login_required
def modifier_preuve(request, preuve_id):
    """Modifier une preuve existante."""
    preuve = get_object_or_404(PreuveRealisation, id=preuve_id)

    if request.method == 'POST':
        form = PreuveRealisationForm(request.POST, request.FILES, instance=preuve)
        if form.is_valid():
            form.save()
            messages.success(request, 'Preuve modifiée avec succès.')
            return redirect('preuves_activite', activite_id=preuve.activite.id)
    else:
        form = PreuveRealisationForm(instance=preuve)

    context = {
        'activite': preuve.activite,
        'form': form,
        'preuve': preuve,
        'title': f"Modifier preuve - {preuve.titre}",
        'is_edit': True,
    }
    return render(request, 'planning/preuves_activite.html', context)


@login_required
def supprimer_preuve(request, preuve_id):
    """Supprimer une preuve."""
    preuve = get_object_or_404(PreuveRealisation, id=preuve_id)
    activite_id = preuve.activite.id
    if preuve.fichier:
        preuve.fichier.delete(save=False)
    preuve.delete()
    messages.success(request, 'Preuve supprimée avec succès.')
    return redirect('preuves_activite', activite_id=activite_id)
=======
def _can_manage_preuves(user, activite):
    if not user.is_authenticated:
        return False
    if user.role in ['point_focal', 'responsable']:
        return activite.point_focal == user or activite.responsable == user
    return False


def preuve_liste(request, activite_id):
    activite = get_object_or_404(Activite, id=activite_id)
    preuves = activite.preuves.all()
    data = []
    for p in preuves:
        data.append({
            'id': p.id,
            'type': p.type,
            'type_display': p.get_type_display(),
            'fichier_url': p.fichier.url if p.fichier else None,
            'url': p.url,
            'description': p.description or '',
            'uploaded_by': f"{p.uploaded_by.first_name} {p.uploaded_by.last_name}" if p.uploaded_by else 'Inconnu',
            'can_delete': _can_manage_preuves(request.user, activite),
        })
    return JsonResponse({'success': True, 'preuves': data})


def preuve_ajouter(request, activite_id):
    activite = get_object_or_404(Activite, id=activite_id)
    if not _can_manage_preuves(request.user, activite):
        return JsonResponse({'success': False, 'message': "Vous n'avez pas la permission d'ajouter une preuve."}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'}, status=405)

    type_preuve = request.POST.get('type')
    annee = request.POST.get('annee')
    description = request.POST.get('description', '').strip()

    if type_preuve not in ['document', 'lien', 'image', 'video']:
        return JsonResponse({'success': False, 'message': 'Type de preuve invalide.'}, status=400)

    try:
        annee = int(annee)
    except (TypeError, ValueError):
        return JsonResponse({'success': False, 'message': 'Année invalide.'}, status=400)

    fichier = request.FILES.get('fichier')
    url = request.POST.get('url', '').strip()

    if activite.preuves.count() >= 10:
        return JsonResponse({'success': False, 'message': 'Cette activité a déjà atteint la limite de 10 preuves.'}, status=400)

    try:
        preuve = PreuveRealisation(
            activite=activite,
            type=type_preuve,
            annee=annee,
            description=description,
            uploaded_by=request.user,
        )
        if type_preuve == 'lien':
            preuve.url = url
            preuve.fichier = None
        else:
            preuve.fichier = fichier
            preuve.url = ''
        preuve.full_clean()
        preuve.save()
    except ValidationError as e:
        return JsonResponse({'success': False, 'message': ' '.join(e.messages)}, status=400)
    except Exception as e:
        logger.error(f"Erreur ajout preuve : {e}", exc_info=True)
        return JsonResponse({'success': False, 'message': 'Erreur lors de la sauvegarde.'}, status=500)

    return JsonResponse({
        'success': True,
        'message': 'Preuve ajoutée.',
        'preuve': {
            'id': preuve.id,
            'type': preuve.type,
            'type_display': preuve.get_type_display(),
            'fichier_url': preuve.fichier.url if preuve.fichier else None,
            'url': preuve.url,
            'description': preuve.description or '',
            'uploaded_by': f"{preuve.uploaded_by.first_name} {preuve.uploaded_by.last_name}" if preuve.uploaded_by else 'Inconnu',
        }
    })


def preuve_supprimer(request, preuve_id):
    preuve = get_object_or_404(PreuveRealisation, id=preuve_id)
    if not _can_manage_preuves(request.user, preuve.activite):
        return JsonResponse({'success': False, 'message': "Vous n'avez pas la permission de supprimer cette preuve."}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'}, status=405)

    try:
        if preuve.fichier:
            preuve.fichier.delete(save=False)
        preuve.delete()
    except Exception as e:
        logger.error(f"Erreur suppression preuve : {e}", exc_info=True)
        return JsonResponse({'success': False, 'message': 'Erreur lors de la suppression.'}, status=500)

    return JsonResponse({'success': True, 'message': 'Preuve supprimée.'})


def _annees_trimestres_for_plan(plan):
    annees = [plan.annee_debut + i for i in range(plan.horizon)]
    return annees


def generer_rapport(request, plan_id):
    plan = get_object_or_404(PlanAction, id=plan_id)
    annees = _annees_trimestres_for_plan(plan)
    trimestres = ['T1', 'T2', 'T3', 'T4']

    if not request.user.is_authenticated:
        return render(request, 'planning/access_denied.html')

    if request.method == 'POST':
        try:
            annee = int(request.POST.get('annee'))
            trimestre = request.POST.get('trimestre')
            if annee not in annees or trimestre not in trimestres:
                messages.error(request, "Année ou trimestre invalide.")
                return redirect('generer_rapport', plan_id=plan.id)

            report_id = generate_quarterly_report(plan_id, annee, trimestre, request.user.id)
            messages.success(request, f"Rapport {trimestre} {annee} généré et envoyé aux acteurs du plan.")
            return redirect('rapport_liste', plan_id=plan.id)
        except Exception as e:
            logger.error(f"Erreur lancement rapport : {e}", exc_info=True)
            messages.error(request, "Erreur lors du lancement de la génération.")

    context = {
        'plan': plan,
        'annees': annees,
        'trimestres': trimestres,
    }
    return render(request, 'planning/generer_rapport.html', context)


def rapport_liste(request, plan_id):
    plan = get_object_or_404(PlanAction, id=plan_id)
    rapports = plan.rapports.all()
    return render(request, 'planning/rapport_liste.html', {
        'plan': plan,
        'rapports': rapports,
    })


def rapport_telecharger(request, rapport_id):
    rapport = get_object_or_404(QuarterlyReport, id=rapport_id)
    if not request.user.is_authenticated:
        return render(request, 'planning/access_denied.html')
    if not rapport.fichier:
        messages.error(request, "Aucun fichier associé.")
        return redirect('rapport_liste', plan_id=rapport.plan.id)
    return redirect(rapport.fichier.url)
>>>>>>> 9800f3858682969e9bcf877aa3d23c715dbb2ea2
