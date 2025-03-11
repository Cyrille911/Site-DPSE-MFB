from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.mail import send_mail
from datetime import datetime

# Modèle PlanAction
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
                couts[i] += cout
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
        # Initialisation de statut_pao
        if not isinstance(self.statut_pao, list) or len(self.statut_pao) != self.horizon:
            self.statut_pao = ["Non entamé"] * self.horizon

        # Gestion de l'année en cours
        current_year = datetime.now().year
        index_annee_courante = current_year - self.annee_debut
        if 0 <= index_annee_courante < self.horizon:
            self.statut_pao[index_annee_courante] = "En cours"
            for i in range(index_annee_courante):
                self.statut_pao[i] = "Achevé"

        # Génération de la référence avant sauvegarde
        if not self.reference:
            if not self.pk:  # Nouvelle instance
                position = PlanAction.objects.count() + 1
            else:  # Instance existante
                position = list(PlanAction.objects.order_by('id')).index(self) + 1
            self.reference = f"PA{position}"

        super().save(*args, **kwargs)

        # Mise à jour des références des enfants
        for effet in self.plan_effet.all():
            effet.update_reference()

    def is_en_cours(self):
        return "En cours" in self.statut_pao

    def __str__(self):
        return f"Plan d'actions {self.reference} : {self.titre}"

# Modèle Effet
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
                couts[i] += cout
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
        if not self.reference:
            if not self.pk:  # Nouvelle instance
                position = self.plan.plan_effet.count() + 1
            else:  # Instance existante
                position = list(self.plan.plan_effet.order_by('id')).index(self) + 1
            self.reference = f"{position}"  # Référence simple : 1, 2, etc.

    def save(self, *args, **kwargs):
        old_instance = None
        if self.pk:
            old_instance = Effet.objects.get(pk=self.pk)

        self.full_clean()
        if not self.reference:
            self.update_reference()
        super().save(*args, **kwargs)

        # Mise à jour des enfants
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

# Modèle Produit
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
                couts[i] += cout
        self.couts = couts
        self.save()

    def calculer_nombres(self):
        produit_action = self.produit_action.prefetch_related('action_activite')
        self.nombre_actions = produit_action.count()
        self.nombre_activites = sum(action.action_activite.count() for action in produit_action)
        self.save()
        self.effet.calculer_nombres()

    def update_reference(self):
        if not self.reference:
            if not self.pk:  # Nouvelle instance
                position = self.effet.effet_produit.count() + 1
            else:  # Instance existante
                position = list(self.effet.effet_produit.order_by('id')).index(self) + 1
            self.reference = f"{self.effet.reference}.{position}"  # Ex. 1.1, 1.2

    def save(self, *args, **kwargs):
        old_instance = None
        if self.pk:
            old_instance = Produit.objects.get(pk=self.pk)

        self.full_clean()
        if not self.reference:
            self.update_reference()
        super().save(*args, **kwargs)

        # Mise à jour des enfants
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

# Modèle Action
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
                couts[i] += cout
        self.couts = couts
        self.save()

    def calculer_nombres(self):
        self.nombre_activites = self.action_activite.count()
        self.save()
        self.produit.calculer_nombres()

    def update_reference(self):
        if not self.reference:
            if not self.pk:  # Nouvelle instance
                position = self.produit.produit_action.count() + 1
            else:  # Instance existante
                position = list(self.produit.produit_action.order_by('id')).index(self) + 1
            self.reference = f"{self.produit.reference}.{position}"  # Ex. 1.1.1

    def save(self, *args, **kwargs):
        old_instance = None
        if self.pk:
            old_instance = Action.objects.get(pk=self.pk)

        self.full_clean()
        if not self.reference:
            self.update_reference()
        super().save(*args, **kwargs)

        # Mise à jour des enfants
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

# Modèle ActiviteLog
class ActiviteLog(models.Model):
    activite = models.ForeignKey('Activite', on_delete=models.CASCADE, related_name='logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    modifications = models.JSONField()
    statut_apres = models.CharField(max_length=50, choices=[
        ('Draft', 'Brouillon'),
        ('Submitted_SE', 'Soumise au SE'),
        ('Pending_SE', 'En attente SE'),
        ('Réalisée', 'Réalisée'),
        ('Non réalisée', 'Non réalisée'),
        ('Supprimée', 'Supprimée'),
        ('Reprogrammée', 'Reprogrammée'),
        ('Rejeté', 'Rejetée'),
    ])
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log pour {self.activite.titre} par {self.user.username if self.user else 'Inconnu'} - {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']

# Modèle Activite
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
    cibles = models.JSONField(default=list)
    realisation = models.JSONField(default=list)
    couts = models.JSONField(default=list)
    point_focal = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False, blank=False, related_name='point_focal_activites')
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='responsable_activites')
    etat_avancement = models.TextField(default="", blank=True)
    commentaire = models.TextField(default="", blank=True)
    commentaire_se = models.TextField(default="", blank=True)
    reference = models.CharField(max_length=50, blank=True)
    pending_changes = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('Non entamée', 'Non entamée'),
            ('En cours', 'En cours'),
            ('Réalisée', 'Réalisée'),
            ('Non réalisée', 'Non réalisée'),
            ('Supprimée', 'Supprimée'),
            ('Reprogrammée', 'Reprogrammée'),
            ('Pending_SE', 'En attente SE'),
            ('Submitted_SE', 'Soumise au SE'),
        ],
        default='Non entamée'
    )
    matrix_status = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        horizon = self.action.produit.effet.plan.horizon
        for field in ['cibles', 'realisation', 'couts', 'matrix_status']:
            value = getattr(self, field)
            if not isinstance(value, list) or len(value) != horizon:
                raise ValidationError(f"'{field}' doit être une liste de {horizon} éléments.")
        if not all(isinstance(x, (str, type(None))) for x in self.cibles):
            raise ValidationError("'cibles' doit contenir des chaînes ou None.")
        if not all(isinstance(x, str) for x in self.realisation):
            raise ValidationError("'realisation' doit contenir des chaînes.")
        if not all(isinstance(x, (int, float)) for x in self.couts):
            raise ValidationError("'couts' doit contenir des nombres décimaux.")
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
        if not self.matrix_status or len(self.matrix_status) != horizon:
            self.matrix_status = ['En cours'] * horizon

        self.full_clean()

        # Génération de la référence
        if not self.reference:
            if not self.pk:  # Nouvelle instance
                position = self.action.action_activite.count() + 1
            else:  # Instance existante
                position = list(self.action.action_activite.order_by('id')).index(self) + 1
            self.reference = f"{self.action.reference}.{position}"  # Ex. 1.1.1.1

        super().save(*args, **kwargs)

        # Mise à jour des calculs en cascade
        self.action.calculer_nombres()
        self.action.calculer_couts()

        # Log des modifications
        if old_instance and user:
            changes = {
                field: getattr(self, field)
                for field in ['etat_avancement', 'realisation', 'commentaire', 'status', 'commentaire_se', 'matrix_status']
                if getattr(self, field) != getattr(old_instance, field)
            }
            if changes:
                ActiviteLog.objects.create(
                    activite=self,
                    user=user,
                    modifications=changes,
                    statut_apres=self.status
                )
                if 'status' in changes and user != self.point_focal and user != self.responsable:
                    recipients = [self.point_focal.email] if self.point_focal.email else []
                    if self.responsable and self.responsable.email:
                        recipients.append(self.responsable.email)
                    if recipients:
                        send_mail(
                            f"Changement de statut pour {self.reference}",
                            f"L'activité {self.reference} - {self.titre} est passée à {self.status}.",
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
        if self.pending_changes:
            self.etat_avancement = self.pending_changes.get('etat_avancement', self.etat_avancement)
            self.realisation = self.pending_changes.get('realisation', self.realisation)
            self.commentaire = self.pending_changes.get('commentaire', self.commentaire)
            self.pending_changes = {}
        self.save(user=user)

    def submit_to_se(self, user):
        if user != self.responsable:
            raise PermissionError("Seul le responsable peut soumettre au SE.")
        self.validate_by_responsable(user)
        self.status = 'Pending_SE'
        self.save(user=user)

    def update_reference(self):
        if not self.reference:
            if not self.pk:  # Nouvelle instance
                position = self.action.action_activite.count() + 1
            else:  # Instance existante
                position = list(self.action.action_activite.order_by('id')).index(self) + 1
            self.reference = f"{self.action.reference}.{position}"  # Ex. 1.1.1.1

    def update_matrix_status(self, annee_index, matrix_version):
        current_version = {
            'etat_avancement': self.etat_avancement,
            'realisation': self.realisation[annee_index],
            'commentaire': self.commentaire,
        }
        self.matrix_status[annee_index] = 'Validé' if current_version == matrix_version else 'En cours'
        self.save()

    def __str__(self):
        return f"Activité {self.reference} : {self.titre}"