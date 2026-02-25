from django.db import models
from django.core.exceptions import ValidationError, PermissionDenied
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from django.http import HttpRequest
import logging
from threading import Timer
from collections import defaultdict

logger = logging.getLogger(__name__)

User = get_user_model()


# Modèle PlanAction (inchangé)
class PlanAction(models.Model):
    id = models.AutoField(primary_key=True)
    titre = models.CharField(max_length=255)
    impact = models.TextField()
    annee_debut = models.PositiveIntegerField(default=2025)
    horizon = models.PositiveIntegerField()
    couts = models.JSONField(default=list)
    statut_pao = models.JSONField(default=list)
    nombre_effets = models.PositiveIntegerField(default=0)
    nombre_produits = models.PositiveIntegerField(default=0)
    nombre_actions = models.PositiveIntegerField(default=0)
    nombre_activites = models.PositiveIntegerField(default=0)
    reference = models.CharField(max_length=50, blank=True)

    def calculer_couts(self):
        couts = [0.0] * self.horizon
        for effet in self.plan_effet.all():
            for i, cout in enumerate(effet.couts):
                couts[i] += float(cout)
        self.couts = couts
        self.save()

    def calculer_nombres(self):
        plan_effet = self.plan_effet.prefetch_related('effet_produit__produit_action__action_activite')
        self.nombre_effets = plan_effet.count()
        self.nombre_produits = sum(effet.effet_produit.count() for effet in plan_effet)
        self.nombre_actions = sum(produit.produit_action.count() for effet in plan_effet for produit in effet.effet_produit.all())
        self.nombre_activites = sum(action.action_activite.count() for effet in plan_effet for produit in effet.effet_produit.all() for action in produit.produit_action.all())
        self.save()

    def save(self, *args, **kwargs):
        if not self.couts or len(self.couts) != self.horizon:
            self.couts = [0.0] * self.horizon
        
        if not isinstance(self.statut_pao, list) or len(self.statut_pao) != self.horizon:
            self.statut_pao = ["Non entamé"] * self.horizon
        current_year = datetime.now().year
        index_annee_courante = current_year - self.annee_debut
        if 0 <= index_annee_courante < self.horizon:
            self.statut_pao[index_annee_courante] = "En cours"
            for i in range(index_annee_courante):
                self.statut_pao[i] = "Achevé"
        
        if not self.reference:
            if not self.pk:
                position = PlanAction.objects.count() + 1
            else:
                position = list(PlanAction.objects.order_by('id')).index(self) + 1
            self.reference = f"PA{position}"
        
        super().save(*args, **kwargs)
        for effet in self.plan_effet.all():
            effet.update_reference()

    def is_en_cours(self):
        return "En cours" in self.statut_pao

    def __str__(self):
        return f"Plan d'actions {self.reference} : {self.titre}"

# Modèle Effet (inchangé)
class Effet(models.Model):
    id = models.AutoField(primary_key=True)
    plan = models.ForeignKey(PlanAction, related_name="plan_effet", on_delete=models.CASCADE)
    titre = models.CharField(max_length=255)
    couts = models.JSONField(default=list)
    nombre_produits = models.PositiveIntegerField(default=0)
    nombre_actions = models.PositiveIntegerField(default=0)
    nombre_activites = models.PositiveIntegerField(default=0)
    reference = models.CharField(max_length=50, blank=True)

    def calculer_couts(self):
        couts = [0.0] * self.plan.horizon
        for produit in self.effet_produit.all():
            for i, cout in enumerate(produit.couts):
                couts[i] += float(cout)
        self.couts = couts
        self.save()
        self.plan.calculer_couts()

    def calculer_nombres(self):
        effet_produit = self.effet_produit.prefetch_related('produit_action__action_activite')
        self.nombre_produits = effet_produit.count()
        self.nombre_actions = sum(produit.produit_action.count() for produit in effet_produit)
        self.nombre_activites = sum(action.action_activite.count() for produit in effet_produit for action in produit.produit_action.all())
        self.save()
        self.plan.calculer_nombres()

    def update_reference(self):
        if not self.reference or self.pk is None:
            if not self.pk:
                position = self.plan.plan_effet.count() + 1
            else:
                position = list(self.plan.plan_effet.order_by('id')).index(self) + 1
            self.reference = f"{position}"
            self.save(update_fields=['reference'])
        for produit in self.effet_produit.all():
            produit.update_reference()

    def save(self, *args, **kwargs):
        if not self.couts or len(self.couts) != self.plan.horizon:
            self.couts = [0.0] * self.plan.horizon
        
        old_instance = None
        if self.pk:
            old_instance = Effet.objects.get(pk=self.pk)
        self.full_clean()
        super().save(*args, **kwargs)
        for produit in self.effet_produit.all():
            produit.update_reference()
        if old_instance and old_instance.plan != self.plan:
            old_instance.plan.calculer_nombres()
            old_instance.plan.calculer_couts()
        self.plan.calculer_nombres()
        self.plan.calculer_couts()

    def delete(self, *args, **kwargs):
        plan = self.plan
        super().delete(*args, **kwargs)
        plan.calculer_nombres()
        plan.calculer_couts()

    def __str__(self):
        return f"Effet {self.reference} : {self.titre}"

# Modèle Produit (inchangé)
class Produit(models.Model):
    id = models.AutoField(primary_key=True)
    effet = models.ForeignKey(Effet, related_name="effet_produit", on_delete=models.CASCADE)
    titre = models.CharField(max_length=255)
    couts = models.JSONField(default=list)
    nombre_actions = models.PositiveIntegerField(default=0)
    nombre_activites = models.PositiveIntegerField(default=0)
    reference = models.CharField(max_length=50, blank=True)

    def calculer_couts(self):
        couts = [0.0] * self.effet.plan.horizon
        for action in self.produit_action.all():
            for i, cout in enumerate(action.couts):
                couts[i] += float(cout)
        self.couts = couts
        self.save()
        self.effet.calculer_couts()

    def calculer_nombres(self):
        produit_action = self.produit_action.prefetch_related('action_activite')
        self.nombre_actions = produit_action.count()
        self.nombre_activites = sum(action.action_activite.count() for action in produit_action)
        self.save()
        self.effet.calculer_nombres()

    def update_reference(self):
        if not self.reference or self.pk is None:
            if not self.pk:
                position = self.effet.effet_produit.count() + 1
            else:
                position = list(self.effet.effet_produit.order_by('id')).index(self) + 1
            self.reference = f"{self.effet.reference}.{position}"
            self.save(update_fields=['reference'])
        for action in self.produit_action.all():
            action.update_reference()

    def save(self, *args, **kwargs):
        if not self.couts or len(self.couts) != self.effet.plan.horizon:
            self.couts = [0.0] * self.effet.plan.horizon
        
        old_instance = None
        if self.pk:
            old_instance = Produit.objects.get(pk=self.pk)
        self.full_clean()
        super().save(*args, **kwargs)
        for action in self.produit_action.all():
            action.update_reference()
        if old_instance and old_instance.effet != self.effet:
            old_instance.effet.calculer_nombres()
            old_instance.effet.calculer_couts()
        self.effet.calculer_nombres()
        self.effet.calculer_couts()

    def delete(self, *args, **kwargs):
        effet = self.effet
        super().delete(*args, **kwargs)
        effet.calculer_nombres()
        effet.calculer_couts()

    def __str__(self):
        return f"Produit {self.reference} : {self.titre}"

# Modèle Action (inchangé)
class Action(models.Model):
    id = models.AutoField(primary_key=True)
    produit = models.ForeignKey(Produit, related_name="produit_action", on_delete=models.CASCADE)
    titre = models.CharField(max_length=255)
    couts = models.JSONField(default=list)
    nombre_activites = models.PositiveIntegerField(default=0)
    reference = models.CharField(max_length=50, blank=True)

    def calculer_couts(self):
        couts = [0.0] * self.produit.effet.plan.horizon
        for activite in self.action_activite.all():
            for i, cout in enumerate(activite.couts):
                couts[i] += float(cout)
        self.couts = couts
        self.save()
        self.produit.calculer_couts()

    def calculer_nombres(self):
        self.nombre_activites = self.action_activite.count()
        self.save()
        self.produit.calculer_nombres()

    def update_reference(self):
        if not self.reference or self.pk is None:
            if not self.pk:
                position = self.produit.produit_action.count() + 1
            else:
                position = list(self.produit.produit_action.order_by('id')).index(self) + 1
            self.reference = f"{self.produit.reference}.{position}"
            self.save(update_fields=['reference'])
        for activite in self.action_activite.all():
            activite.update_reference()

    def save(self, *args, **kwargs):
        if not self.couts or len(self.couts) != self.produit.effet.plan.horizon:
            self.couts = [0.0] * self.produit.effet.plan.horizon
        
        old_instance = None
        if self.pk:
            old_instance = Action.objects.get(pk=self.pk)
        self.full_clean()
        super().save(*args, **kwargs)
        for activite in self.action_activite.all():
            activite.update_reference()
        if old_instance and old_instance.produit != self.produit:
            old_instance.produit.calculer_nombres()
            old_instance.produit.calculer_couts()
        self.produit.calculer_nombres()
        self.produit.calculer_couts()

    def delete(self, *args, **kwargs):
        produit = self.produit
        super().delete(*args, **kwargs)
        produit.calculer_nombres()
        produit.calculer_couts()

    def __str__(self):
        return f"Action {self.reference} : {self.titre}"

# Modèle Activite
# File d'attente temporaire pour regrouper les notifications
class NotificationQueue:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NotificationQueue, cls).__new__(cls)
            cls._instance.pending_notifications = defaultdict(list)
            cls._instance.timer = None
        return cls._instance

    def add_activity(self, activite, user):
        recipients = tuple(sorted(self._get_recipients(activite, user)))
        self.pending_notifications[recipients].append(activite)
        if not self.timer or not self.timer.is_alive():
            self.timer = Timer(60.0, self.send_grouped_notifications)
            self.timer.start()
            logger.debug("Timer démarré pour l'envoi groupé des notifications.")

    def _get_recipients(self, activite, user):
        recipients = set()
        if activite.point_focal and activite.point_focal.email:
            recipients.add(activite.point_focal.email)
        if activite.responsable and activite.responsable.email:
            recipients.add(activite.responsable.email)
        if user.email:
            recipients.add(user.email)
        return recipients

    def send_grouped_notifications(self):
        for recipients, activites in self.pending_notifications.items():
            if not recipients:
                continue

            # Construire une liste de destinataires mise à jour avec suiveurs et évaluateurs
            all_recipients = set(recipients)  # Convertir en set pour éviter les doublons
            for activite in activites:
                plan = activite.action.produit.effet.plan  # Accès au PlanAction

                # Ajouter les suiveurs (supposons qu'ils sont dans une relation ManyToMany ou ForeignKey)
                if hasattr(plan, 'suiveurs') and plan.suiveurs.exists():
                    suiveurs_emails = [suiveur.email for suiveur in plan.suiveurs.all() if suiveur.email]
                    all_recipients.update(suiveurs_emails)

                # Ajouter les évaluateurs (supposons qu'ils sont dans une relation ManyToMany ou ForeignKey)
                if hasattr(plan, 'evaluateurs') and plan.evaluateurs.exists():
                    evaluateurs_emails = [evaluateur.email for evaluateur in plan.evaluateurs.all() if evaluateur.email]
                    all_recipients.update(evaluateurs_emails)

            if not all_recipients:
                logger.debug("Aucun destinataire valide trouvé pour les notifications.")
                continue

            subject = f"Notification : Création de {len(activites)} nouvelle(s) activité(s)"
            message = (
                "Bonjour,\n\n"
                "Nous avons le plaisir de vous informer que les activités suivantes ont été récemment créées dans le cadre du plan d’action. Voici les détails :\n\n"
            )

            for activite in activites:
                plan = activite.action.produit.effet.plan
                annee_debut = plan.annee_debut
                horizon = plan.horizon
                annees = [annee_debut + i for i in range(horizon)]

                message += f"**Activité : {activite.titre}**\n"
                message += f"- Référence : {activite.reference or 'Non spécifiée'}\n"
                message += f"- Type : {activite.type or 'Non défini'}\n"
                message += f"- Indicateur : {activite.indicateur_label} (Réf. : {activite.indicateur_reference or 'N/A'})\n"

                # Afficher les coûts par année
                message += "- Coûts prévus :\n"
                for i, cout in enumerate(activite.couts[:horizon]):
                    message += f"  * {annees[i]} : {cout if cout is not None else 'Non défini'} \n"

                # Afficher les cibles par année
                message += "- Cibles :\n"
                for i, cible in enumerate(activite.cibles[:horizon]):
                    message += f"  * {annees[i]} : {cible if cible is not None else 'Non définie'} \n"

                # Gérer les périodes d'exécution
                periodes = activite.periodes_execution
                if periodes and isinstance(periodes, list) and periodes[0]:
                    if isinstance(periodes[0], list):  # Liste imbriquée
                        periodes_flat = periodes[0]
                    else:
                        periodes_flat = periodes
                    message += f"- Périodes d'exécution : {', '.join(periodes_flat)}\n\n"
                else:
                    message += "- Périodes d'exécution : Non spécifiées\n\n"

            message += (
                "N’hésitez pas à nous contacter si vous avez des questions ou besoin de précisions.\n\n"
                "Cordialement,\n"
                "L’équipe de gestion du plan d’action"
            )

            logger.debug(f"Envoi de notification groupée - Sujet: {subject}, Destinataires: {list(all_recipients)}")
            send_mail(
                subject=subject,
                message=message,
                from_email='cyrilletaha01@gmail.com',
                recipient_list=list(all_recipients),  # Utiliser la liste mise à jour
                fail_silently=True
            )

        self.pending_notifications.clear()
        logger.debug("File d'attente vidée après envoi groupé.")

class Activite(models.Model):
    id = models.AutoField(primary_key=True)
    reference = models.CharField(max_length=50, blank=True)
    titre = models.CharField(max_length=255)
    type = models.CharField(
        max_length=50,
        choices=[
            ('Réforme', 'Réforme'),
            ('Investissement', 'Investissement'),
            ('Etude', 'Etude'),
            ('Texte', 'Texte'),
            ('Activité ordinaire', 'Activité ordinaire')
        ]
    )
    
    action = models.ForeignKey('Action', related_name="action_activite", on_delete=models.CASCADE)
    point_focal = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='point_focal_activites'
    )
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,  # Suppression du responsable met le champ à NULL
        null=True,  # Doit être nullable pour SET_NULL
        blank=True,
        related_name='responsable_activites'
    )
    
    indicateur_label = models.CharField(max_length=255)
    indicateur_reference = models.CharField(max_length=255)
    structure = models.CharField(max_length=255, null=False, blank=False, help_text="Structure responsable de l'activité")
    
    cibles = models.JSONField(default=list)
    realisation = models.JSONField(default=list)
    couts = models.JSONField(default=list)
    periodes_execution = models.JSONField(default=list)
    etat_avancement = models.JSONField(default=list)
    commentaire = models.JSONField(default=list)
    commentaire_se = models.JSONField(default=list)
    pending_changes = models.JSONField(default=list)
    proposed_changes = models.JSONField(default=list)
    status = models.JSONField(default=list)
    matrix_status = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    alertes_envoyees = models.JSONField(default=dict, blank=True, null=True)

    class Meta:
        verbose_name = "Activité"
        verbose_name_plural = "Activités"

    def __str__(self):
        return f"Activité {self.reference} : {self.titre}"

    def clean(self):
        horizon = self.action.produit.effet.plan.horizon
        fields_to_check = [
            'cibles', 'realisation', 'couts', 'periodes_execution', 'etat_avancement',
            'commentaire', 'commentaire_se', 'pending_changes', 'proposed_changes', 'status', 'matrix_status'
        ]
        for field in fields_to_check:
            value = getattr(self, field)
            if not isinstance(value, list) or len(value) != horizon:
                raise ValidationError(f"'{field}' doit être une liste de {horizon} éléments.")

        if not all(isinstance(x, (str, type(None))) for x in self.cibles):
            raise ValidationError("'cibles' doit contenir des chaînes ou None.")
        if not all(isinstance(x, str) for x in self.realisation):
            raise ValidationError("'realisation' doit contenir des chaînes.")
        if not all(isinstance(x, (int, float)) for x in self.couts):
            raise ValidationError("'couts' doit contenir des nombres décimaux.")
        if not all(isinstance(x, list) and all(t in ['T1', 'T2', 'T3', 'T4'] for t in x) for x in self.periodes_execution):
            raise ValidationError("'periodes_execution' doit contenir des listes de 'T1', 'T2', 'T3', 'T4'.")
        if not all(isinstance(x, str) for x in self.etat_avancement):
            raise ValidationError("'etat_avancement' doit contenir des chaînes.")
        if not all(isinstance(x, str) for x in self.commentaire):
            raise ValidationError("'commentaire' doit contenir des chaînes.")
        if not all(isinstance(x, str) for x in self.commentaire_se):
            raise ValidationError("'commentaire_se' doit contenir des chaînes.")
        if not all(isinstance(x, dict) for x in self.pending_changes):
            raise ValidationError("'pending_changes' doit contenir des dictionnaires.")
        if not all(isinstance(x, dict) for x in self.proposed_changes):
            raise ValidationError("'proposed_changes' doit contenir des dictionnaires.")
        if not all(x in ['Non entamée', 'En cours', 'Réalisée', 'Non réalisée', 'Supprimée', 'Reprogrammée'] for x in self.status):
            raise ValidationError("'status' doit contenir des valeurs valides.")
        if not all(x in ['En cours', 'Validée'] for x in self.matrix_status):
            raise ValidationError("'matrix_status' doit être 'En cours' ou 'Validée'.")

    def _send_change_notification(self, user):
        subject = f"Modification proposée pour l'activité {self.reference}"
        if user == self.responsable:
            recipients = [u.email for u in User.objects.filter(groups__name='SuiveurEvaluateur') if u.email]
            message = (
                f"Le responsable {user.email} a proposé des modifications pour l'activité {self.reference}.\n"
                f"Titre : {self.titre}\n"
                f"Référence : {self.reference}\n"
                f"Consultez les détails dans le système."
            )
        elif user == self.point_focal:
            recipients = []
            if self.responsable and self.responsable.email:
                recipients.append(self.responsable.email)
            message = (
                f"Le point focal {user.email} a proposé des modifications pour l'activité {self.reference}.\n"
                f"Titre : {self.titre}\n"
                f"Référence : {self.reference}\n"
                f"Consultez les détails dans le système."
            )
        elif user.groups.filter(name='SuiveurEvaluateur').exists():
            recipients = []
            if self.responsable and self.responsable.email:
                recipients.append(self.responsable.email)
            if self.point_focal and self.point_focal.email:
                recipients.add(self.point_focal.email)
            message = (
                f"Un suiveur-évaluateur {user.email} a proposé des modifications pour l'activité {self.reference}.\n"
                f"Titre : {self.titre}\n"
                f"Référence : {self.reference}\n"
                f"Consultez les détails dans le système."
            )
        else:
            return

        if recipients:
            logger.debug(f"Envoi de notification de changement - Sujet: {subject}, Destinataires: {recipients}")
            send_mail(
                subject=subject,
                message=message,
                from_email='cyrilletaha01@gmail.com',
                recipient_list=recipients,
                fail_silently=True
            )
        else:
            logger.debug("Aucun destinataire valide trouvé pour la notification de changement.")

    def update_responsables(self):
        """Met à jour dynamiquement le responsable en fonction de la structure de l'activité."""
        if self.structure:
            # Recherche du point focal pour cette structure (un seul par structure)
            point_focal = User.objects.filter(
                entity=self.structure,
                role='point_focal'
            ).first()
            
            # Recherche du responsable pour cette structure (différent du point focal)
            responsable = User.objects.filter(
                entity=self.structure,
                role='responsable'
            ).first()
            
            # Toujours assigner le point focal s'il existe
            if point_focal:
                self.point_focal = point_focal
            else:
                self.point_focal = None
            
            # Toujours assigner le responsable s'il existe
            if responsable:
                self.responsable = responsable
            else:
                self.responsable = None
        else:
            # Si pas de structure définie, mettre les champs à None
            self.point_focal = None
            self.responsable = None

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        apply_changes = kwargs.pop('apply_changes', False)
        
        old_instance = None
        if self.pk:
            old_instance = Activite.objects.get(pk=self.pk)
            if old_instance.indicateur_reference != self.indicateur_reference:
                self.indicateur_reference = old_instance.indicateur_reference

        horizon = self.action.produit.effet.plan.horizon
        if not self.couts or len(self.couts) != horizon:
            self.couts = [0.0] * horizon
        if not self.cibles or len(self.cibles) != horizon:
            self.cibles = ["Non définie"] * horizon
        if not self.realisation or len(self.realisation) != horizon:
            self.realisation = ["En attente"] * horizon
        if not self.periodes_execution or len(self.periodes_execution) != horizon:
            self.periodes_execution = [[] for _ in range(horizon)]
        if not self.etat_avancement or len(self.etat_avancement) != horizon:
            self.etat_avancement = ["En attente"] * horizon
        if not self.commentaire or len(self.commentaire) != horizon:
            self.commentaire = ["En attente"] * horizon
        if not self.commentaire_se or len(self.commentaire_se) != horizon:
            self.commentaire_se = ["En attente"] * horizon
        if not self.pending_changes or len(self.pending_changes) != horizon:
            self.pending_changes = [{}] * horizon
        if not self.proposed_changes or len(self.proposed_changes) != horizon:
            self.proposed_changes = [{}] * horizon
        if not self.status or len(self.status) != horizon:
            self.status = ["Non entamée"] * horizon
        if not self.matrix_status or len(self.matrix_status) != horizon:
            self.matrix_status = ["Validée"] * horizon
        if self.alertes_envoyees is None or not isinstance(self.alertes_envoyees, dict):
            self.alertes_envoyees = {}

        for i in range(horizon):
            if self.pending_changes[i] or self.proposed_changes[i]:
                self.matrix_status[i] = 'En cours'

        # Synchro PF avec Responsable après soumission
        if user == self.responsable and self.pending_changes != old_instance.pending_changes if old_instance else False:
            for i in range(horizon):
                if self.pending_changes[i]:
                    self.proposed_changes[i] = self.pending_changes[i].copy()  # PF suit Responsable

        self.full_clean()
        self.update_reference()

        super().save(*args, **kwargs)

        if user:
            try:
                if not old_instance:
                    NotificationQueue().add_activity(self, user)
                elif (self.pending_changes != old_instance.pending_changes or 
                      self.proposed_changes != old_instance.proposed_changes):
                    self._send_change_notification(user)
            except Exception as e:
                logger.error(f"Erreur lors de la gestion des notifications : {str(e)}", exc_info=True)
        if apply_changes and user:
            self._log_changes(user)

        # Mettre à jour les responsables avant de sauvegarder les changements
        old_point_focal = self.point_focal_id
        old_responsable = self.responsable_id
        self.update_responsables()
        
        # Sauvegarder si les responsables ont changé
        if (self.point_focal_id != old_point_focal or 
            self.responsable_id != old_responsable):
            super().save(update_fields=['point_focal', 'responsable'])

        self.action.calculer_nombres()
        self.action.calculer_couts()

        if not self.reference or self.pk is None:
            if not self.pk:
                position = self.action.action_activite.count() + 1
            else:
                position = list(self.action.action_activite.order_by('id')).index(self) + 1
            self.reference = f"{self.action.reference}.{position}"
            
    def update_reference(self):
        if not self.reference or self.pk is None:
            if not self.pk:
                position = self.action.action_activite.count() + 1
            else:
                position = list(self.action.action_activite.order_by('id')).index(self) + 1
            self.reference = f"{self.action.reference}.{position}"

    def propose_changes(self, user, index, etat_avancement=None, realisation=None, commentaire=None, commentaire_se=None, status=None):
        horizon = self.action.produit.effet.plan.horizon
        if index >= horizon:
            raise ValueError("Index hors de l'horizon du plan.")

        # Restriction : Le point focal ne peut pas modifier si aucun responsable n'est assigné
        if user == self.point_focal and not self.responsable:
            raise PermissionDenied("Vous ne pouvez pas proposer de modifications tant qu'un responsable n'est pas assigné à cette activité.")

        # Assurer que les listes ont la bonne taille
        if len(self.pending_changes) <= index:
            self.pending_changes.extend([{}] * (index + 1 - len(self.pending_changes)))
        if len(self.proposed_changes) <= index:
            self.proposed_changes.extend([{}] * (index + 1 - len(self.proposed_changes)))
        if len(self.matrix_status) <= index:
            self.matrix_status.extend(['En cours'] * (index + 1 - len(self.matrix_status)))

        if user == self.responsable or user.groups.filter(name='SuiveurEvaluateur').exists():
            # Gestion pour Responsable ou Suiveur/Évaluateur : mise à jour de pending_changes et écrasement de proposed_changes
            if not self.pending_changes[index]:
                self.pending_changes[index] = {
                    'etat_avancement': self.etat_avancement[index],
                    'realisation': self.realisation[index],
                    'commentaire': self.commentaire[index],
                    'commentaire_se': self.commentaire_se[index],
                    'status': self.status[index],
                    'last_modified_by': user.username,
                    'is_processed_by_se': user.groups.filter(name='SuiveurEvaluateur').exists()
                }
            if etat_avancement is not None:
                self.pending_changes[index]['etat_avancement'] = etat_avancement
            if realisation is not None:
                self.pending_changes[index]['realisation'] = realisation
            if commentaire is not None:
                self.pending_changes[index]['commentaire'] = commentaire
            if commentaire_se is not None:
                self.pending_changes[index]['commentaire_se'] = commentaire_se
            if status is not None:
                if status not in ['Non entamée', 'En cours', 'Réalisée', 'Non réalisée', 'Supprimée', 'Reprogrammée']:
                    raise ValueError("Statut invalide.")
                self.pending_changes[index]['status'] = status
            self.pending_changes[index]['last_modified_by'] = user.username
            self.pending_changes[index]['is_processed_by_se'] = user.groups.filter(name='SuiveurEvaluateur').exists()
            self.matrix_status[index] = 'En cours'
            # Écraser proposed_changes avec les valeurs de pending_changes
            self.proposed_changes[index] = self.pending_changes[index].copy()
        elif user == self.point_focal:
            # Gestion pour Point Focal : mise à jour de proposed_changes uniquement
            if not self.proposed_changes[index]:
                self.proposed_changes[index] = {
                    'etat_avancement': self.etat_avancement[index],
                    'realisation': self.realisation[index],
                    'commentaire': self.commentaire[index],
                    'last_modified_by': user.username,
                }
            if etat_avancement is not None:
                self.proposed_changes[index]['etat_avancement'] = etat_avancement
            if realisation is not None:
                self.proposed_changes[index]['realisation'] = realisation
            if commentaire is not None:
                self.proposed_changes[index]['commentaire'] = commentaire
            self.proposed_changes[index]['last_modified_by'] = user.username
            self.matrix_status[index] = 'En cours'
        else:
            raise PermissionDenied("Vous n'avez pas les permissions nécessaires pour proposer des changements.")

        self.save(user=user)

    def apply_pending_changes(self, user, index):
        if not user.groups.filter(name='SuiveurEvaluateur').exists():
            raise PermissionDenied("Seul un suiveur-évaluateur peut appliquer les changements définitivement.")
        
        horizon = self.action.produit.effet.plan.horizon
        if index >= horizon or not self.pending_changes[index]:
            raise ValueError("Aucune modification en attente pour cette année.")

        self.etat_avancement[index] = self.pending_changes[index].get('etat_avancement', self.etat_avancement[index])
        self.realisation[index] = self.pending_changes[index].get('realisation', self.realisation[index])
        self.commentaire[index] = self.pending_changes[index].get('commentaire', self.commentaire[index])
        self.commentaire_se[index] = self.pending_changes[index].get('commentaire_se', self.commentaire_se[index])
        self.status[index] = self.pending_changes[index].get('status', self.status[index])
        self.pending_changes[index] = {}
        self.proposed_changes[index] = {}
        self.matrix_status[index] = 'Validée'
        self.save(user=user, apply_changes=True)

    def set_status(self, user, index, status):
        if not user.groups.filter(name='SuiveurEvaluateur').exists():
            raise PermissionDenied("Seul un suiveur-évaluateur peut modifier le statut directement.")
        
        horizon = self.action.produit.effet.plan.horizon
        if index >= horizon:
            raise ValueError("Index hors de l'horizon du plan.")
        
        if status not in ['Non entamée', 'En cours', 'Réalisée', 'Non réalisée', 'Supprimée', 'Reprogrammée']:
            raise ValueError("Statut invalide.")
        
        self.status[index] = status
        self.save(user=user)

    def reject_changes(self, user, index):
        if user != self.responsable and not user.groups.filter(name='SuiveurEvaluateur').exists():
            raise PermissionDenied("Seul le responsable ou un suiveur-évaluateur peut rejeter des modifications.")
        
        horizon = self.action.produit.effet.plan.horizon
        if index >= horizon:
            raise ValueError("Index hors de l'horizon du plan.")
        
        self.pending_changes[index] = {}
        self.proposed_changes[index] = {}
        self.matrix_status[index] = 'Validée'
        self.save(user=user)
        self.action.calculer_nombres()
        self.action.calculer_couts()

    @staticmethod
    def update_all_activities_responsables():
        """
        Met à jour le point focal et responsable de toutes les activités
        pour garantir la cohérence après des modifications massives.
        """
        from django.db import transaction
        
        with transaction.atomic():
            activities = Activite.objects.all()
            for activite in activities:
                activite.update_responsables()
                activite.save(update_fields=['point_focal', 'responsable'])

    def delete(self, *args, **kwargs):
        action = self.action
        super().delete(*args, **kwargs)
        action.calculer_nombres()
        action.calculer_couts()

# ... (rest of the code remains the same)
        current_version = {
            'etat_avancement': self.etat_avancement[annee_index],
            'realisation': self.realisation[annee_index],
            'commentaire': self.commentaire[annee_index],
            'status': self.status[annee_index],
        }
        self.matrix_status[annee_index] = 'Validée' if current_version == matrix_version and not self.pending_changes[annee_index] and not self.proposed_changes[annee_index] else 'En cours'
        self.save()

    def get_last_matrix_status_change(self):
        last_log = self.logs.filter(modifications__has_key='matrix_status').order_by('-timestamp').first()
        return last_log.timestamp if last_log else None

    def _log_changes(self, user):
        old_instance = Activite.objects.get(pk=self.pk)
        horizon = self.action.produit.effet.plan.horizon
        for i in range(horizon):
            changes = {}
            for field in ['etat_avancement', 'realisation', 'commentaire', 'commentaire_se', 'status']:
                old_value = getattr(old_instance, field)[i]
                new_value = getattr(self, field)[i]
                if old_value != new_value:
                    changes[field] = {'old': old_value, 'new': new_value}
            if changes:
                ActiviteLog.objects.create(
                    activite=self,
                    user=user,
                    modifications={'year_index': i, 'changes': changes},
                    statut_apres=self.status[i]
                )

    @staticmethod
    def check_activity_alerts():
        today = datetime.now().date()
        current_year = today.year
        current_month = today.month
        current_weekday = today.weekday()

        if current_weekday != 0:
            return

        trimestre_dates = {
            'T1': (datetime(current_year, 3, 31).date(), 3),
            'T2': (datetime(current_year, 6, 30).date(), 6),
            'T3': (datetime(current_year, 9, 30).date(), 9),
            'T4': (datetime(current_year, 12, 31).date(), 12),
        }
        alert_threshold = timedelta(days=15)
        suiveurs = User.objects.filter(is_active=True, groups__name='SuiveurEvaluateur')
        suiveurs_emails = [u.email for u in suiveurs if u.email]

        for activite in Activite.objects.select_related('action__produit__effet__plan').all():
            plan = activite.action.produit.effet.plan
            horizon = plan.horizon
            annee_debut = plan.annee_debut

            for year_index in range(horizon):
                annee = annee_debut + year_index
                if annee != current_year or plan.statut_pao[year_index] != "En cours":
                    continue

                periodes = activite.periodes_execution[year_index]
                if not periodes:
                    continue

                for periode in periodes:
                    fin_trimestre, mois_fin = trimestre_dates[periode]
                    debut_alerte = fin_trimestre - alert_threshold

                    if current_month != mois_fin or not (debut_alerte <= today <= fin_trimestre):
                        continue

                    cle_alerte = f"{annee}-{periode}-{today.isoformat()}"
                    if cle_alerte not in activite.alertes_envoyees:
                        recipients = [activite.point_focal.email] if activite.point_focal.email else []
                        if activite.responsable and activite.responsable.email:
                            recipients.append(activite.responsable.email)
                        if recipients:
                            send_mail(
                                f"Rappel : Activité {activite.reference} - {periode} {annee}",
                                f"L'activité '{activite.titre}' (ref: {activite.reference}) approche sa période d'exécution {periode} pour {annee}. "
                                f"Date de fin : {fin_trimestre}. Veuillez vérifier son état.",
                                settings.DEFAULT_FROM_EMAIL,
                                recipients,
                                fail_silently=True,
                            )
                        if suiveurs_emails:
                            send_mail(
                                f"Rappel : Activité {activite.reference} - {periode} {annee}",
                                f"L'activité '{activite.titre}' (ref: {activite.reference}) approche sa période d'exécution {periode} pour {annee}. "
                                f"Date de fin : {fin_trimestre}.",
                                settings.DEFAULT_FROM_EMAIL,
                                suiveurs_emails,
                                fail_silently=True,
                            )
                        activite.alertes_envoyees[cle_alerte] = today.isoformat()
                        activite.save()

class ActiviteLog(models.Model):
    activite = models.ForeignKey(Activite, on_delete=models.CASCADE, related_name='logs')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    modifications = models.JSONField()
    statut_apres = models.CharField(
        max_length=50,
        choices=[
            ('Non évaluée', 'Non évaluée'),
            ('En cours', 'En cours'),
            ('Réalisée', 'Réalisée'),
            ('Non réalisée', 'Non réalisée'),
            ('Supprimée', 'Supprimée'),
            ('Reprogrammée', 'Reprogrammée'),
        ]
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log pour {self.activite.titre} par {self.user.username if self.user else 'Inconnu'} - {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']