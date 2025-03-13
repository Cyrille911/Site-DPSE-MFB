from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.mail import send_mail
from datetime import datetime

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

    def save(self, *args, **kwargs):
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

    def save(self, *args, **kwargs):
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

    def save(self, *args, **kwargs):
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

# Modèle Activite (mis à jour avec periodes_execution)
class Activite(models.Model):
    id = models.AutoField(primary_key=True)
    action = models.ForeignKey(Action, related_name="action_activite", on_delete=models.CASCADE)
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
    indicateur_label = models.CharField(max_length=255)
    indicateur_reference = models.CharField(max_length=255)
    cibles = models.JSONField(default=list)  # Liste des cibles par année
    realisation = models.JSONField(default=list)  # Liste des réalisations par année
    couts = models.JSONField(default=list)  # Liste des coûts par année
    periodes_execution = models.JSONField(default=list)  # Liste des trimestres par année (ex. ["T1", "T2"])
    point_focal = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False, blank=False, related_name='point_focal_activites')
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='responsable_activites')
    etat_avancement = models.JSONField(default=list)  # Liste des états d'avancement par année
    commentaire = models.JSONField(default=list)  # Liste des commentaires par année
    commentaire_se = models.JSONField(default=list)  # Liste des commentaires SE par année
    reference = models.CharField(max_length=50, blank=True)
    pending_changes = models.JSONField(default=list)  # Liste des changements en attente par année
    status = models.JSONField(default=list)  # Liste des statuts par année
    matrix_status = models.JSONField(default=list)  # Liste des statuts de matrice par année
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        horizon = self.action.produit.effet.plan.horizon
        fields_to_check = ['cibles', 'realisation', 'couts', 'periodes_execution', 'etat_avancement', 
                           'commentaire', 'commentaire_se', 'pending_changes', 'status', 'matrix_status']
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
        if not all(isinstance(x, (dict, type(None))) for x in self.pending_changes):
            raise ValidationError("'pending_changes' doit contenir des dictionnaires ou None.")
        if not all(x in ['Non entamée', 'En cours', 'Réalisée', 'Non réalisée', 'Supprimée', 
                         'Reprogrammée', 'Pending_SE', 'Submitted_SE'] for x in self.status):
            raise ValidationError("'status' doit contenir des valeurs valides.")
        if not all(x in ['En cours', 'Validé'] for x in self.matrix_status):
            raise ValidationError("'matrix_status' doit contenir 'En cours' ou 'Validé'.")

    def get_last_matrix_status_change(self):
        last_log = self.logs.filter(modifications__has_key='matrix_status').order_by('-timestamp').first()
        if last_log:
            return last_log.timestamp
        return None

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        old_instance = None
        if self.pk:
            old_instance = Activite.objects.get(pk=self.pk)
            if old_instance.indicateur_reference != self.indicateur_reference:
                self.indicateur_reference = old_instance.indicateur_reference

        # Initialisation des listes
        horizon = self.action.produit.effet.plan.horizon
        if not self.cibles or len(self.cibles) != horizon:
            self.cibles = [None] * horizon
        if not self.realisation or len(self.realisation) != horizon:
            self.realisation = [""] * horizon
        if not self.couts or len(self.couts) != horizon:
            self.couts = [0.0] * horizon
        if not self.periodes_execution or len(self.periodes_execution) != horizon:
            self.periodes_execution = [[] for _ in range(horizon)]  # Liste vide par année
        if not self.etat_avancement or len(self.etat_avancement) != horizon:
            self.etat_avancement = [""] * horizon
        if not self.commentaire or len(self.commentaire) != horizon:
            self.commentaire = [""] * horizon
        if not self.commentaire_se or len(self.commentaire_se) != horizon:
            self.commentaire_se = [""] * horizon
        if not self.pending_changes or len(self.pending_changes) != horizon:
            self.pending_changes = [{}] * horizon
        if not self.status or len(self.status) != horizon:
            self.status = ["Non entamée"] * horizon
        if not self.matrix_status or len(self.matrix_status) != horizon:
            self.matrix_status = ["En cours"] * horizon

        self.full_clean()

        # Génération de la référence
        if not self.reference or self.pk is None:
            if not self.pk:
                position = self.action.action_activite.count() + 1
            else:
                position = list(self.action.action_activite.order_by('id')).index(self) + 1
            self.reference = f"{self.action.reference}.{position}"

        super().save(*args, **kwargs)

        # Mise à jour des calculs en cascade
        self.action.calculer_nombres()
        self.action.calculer_couts()

        # Log des modifications
        if old_instance and user:
            fields_to_log = ['etat_avancement', 'realisation', 'commentaire', 'status', 
                             'commentaire_se', 'matrix_status', 'pending_changes', 'periodes_execution']
            for year_index in range(horizon):
                changes = {}
                for field in fields_to_log:
                    old_value = getattr(old_instance, field)[year_index]
                    new_value = getattr(self, field)[year_index]
                    if old_value != new_value:
                        changes[field] = {
                            'old': old_value,
                            'new': new_value
                        }
                if changes:
                    ActiviteLog.objects.create(
                        activite=self,
                        user=user,
                        modifications={
                            'year_index': year_index,
                            'changes': changes
                        },
                        statut_apres=self.status[year_index]
                    )
                    if 'status' in changes and user != self.point_focal and user != self.responsable:
                        recipients = [self.point_focal.email] if self.point_focal.email else []
                        if self.responsable and self.responsable.email:
                            recipients.append(self.responsable.email)
                        if recipients:
                            year = self.action.produit.effet.plan.annee_debut + year_index
                            send_mail(
                                f"Changement de statut pour {self.reference} (Année {year})",
                                f"L'activité {self.reference} - {self.titre} est passée de "
                                f"'{changes['status']['old']}' à '{changes['status']['new']}' pour l'année {year}.",
                                settings.DEFAULT_FROM_EMAIL,
                                recipients,
                                fail_silently=True,
                            )

    def delete(self, *args, **kwargs):
        action = self.action
        super().delete(*args, **kwargs)
        action.calculer_nombres()
        action.calculer_couts()

    def validate_by_responsable(self, user):
        if user != self.responsable:
            raise PermissionError("Seul le responsable peut valider.")
        horizon = self.action.produit.effet.plan.horizon
        for i in range(horizon):
            if self.pending_changes[i]:
                self.etat_avancement[i] = self.pending_changes[i].get('etat_avancement', self.etat_avancement[i])
                self.realisation[i] = self.pending_changes[i].get('realisation', self.realisation[i])
                self.commentaire[i] = self.pending_changes[i].get('commentaire', self.commentaire[i])
                self.periodes_execution[i] = self.pending_changes[i].get('periodes_execution', self.periodes_execution[i])
                self.pending_changes[i] = {}
        self.save(user=user)

    def submit_to_se(self, user):
        if user != self.responsable:
            raise PermissionError("Seul le responsable peut soumettre au SE.")
        self.validate_by_responsable(user)
        horizon = self.action.produit.effet.plan.horizon
        for i in range(horizon):
            self.status[i] = 'Pending_SE'
        self.save(user=user)

    def update_reference(self):
        if not self.reference or self.pk is None:
            if not self.pk:
                position = self.action.action_activite.count() + 1
            else:
                position = list(self.action.action_activite.order_by('id')).index(self) + 1
            self.reference = f"{self.action.reference}.{position}"
            self.save(update_fields=['reference'])

    def update_matrix_status(self, annee_index, matrix_version):
        current_version = {
            'etat_avancement': self.etat_avancement[annee_index],
            'realisation': self.realisation[annee_index],
            'commentaire': self.commentaire[annee_index],
            'periodes_execution': self.periodes_execution[annee_index],
        }
        self.matrix_status[annee_index] = 'Validé' if current_version == matrix_version else 'En cours'
        self.save()

    def __str__(self):
        return f"Activité {self.reference} : {self.titre}"

# Modèle ActiviteLog (inchangé)
class ActiviteLog(models.Model):
    activite = models.ForeignKey(Activite, on_delete=models.CASCADE, related_name='logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    modifications = models.JSONField()
    statut_apres = models.CharField(
        max_length=50,
        choices=[
            ('Draft', 'Brouillon'),
            ('Submitted_SE', 'Soumise au SE'),
            ('Pending_SE', 'En attente SE'),
            ('Réalisée', 'Réalisée'),
            ('Non réalisée', 'Non réalisée'),
            ('Supprimée', 'Supprimée'),
            ('Reprogrammée', 'Reprogrammée'),
            ('Rejeté', 'Rejetée'),
        ]
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log pour {self.activite.titre} par {self.user.username if self.user else 'Inconnu'} - {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']