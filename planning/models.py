from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings

def default():
    return [0] * 3  # Génère une liste de trois zéros

class PlanAction(models.Model):
    id = models.AutoField(primary_key=True)
    titre = models.CharField(max_length=255)
    impact = models.TextField()
    annee_debut = models.PositiveIntegerField(default=2025)
    horizon = models.PositiveIntegerField()
    couts = models.JSONField(default=default)
    nombre_effets = models.PositiveIntegerField(default=0)
    nombre_produits = models.PositiveIntegerField(default=0)
    nombre_actions = models.PositiveIntegerField(default=0)
    nombre_activites = models.PositiveIntegerField(default=0)

    def calculer_couts(self):
        """Calcul du coût total du plan en additionnant les coûts de ses effets."""
        couts = [0.0] * self.horizon
        for effet in self.plan_effet.all():
            for i, cout in enumerate(effet.couts):
                couts[i] += cout  # Ajout des coûts des effets
        self.couts = couts
        self.save()

    def calculer_nombres(self):
        """Met à jour le nombre total d'effets, produits, actions et activités."""
        plan_effet = self.plan_effet.prefetch_related(
            'effet_produit__produit_action__action_activite'
        )
        
        self.nombre_effets = plan_effet.count()
        self.nombre_produits = sum(effet.effet_produit.count() for effet in plan_effet)
        self.nombre_actions = sum(produit.produit_action.count() for effet in plan_effet for produit in effet.effet_produit.all())
        self.nombre_activites = sum(action.action_activite.count() for effet in plan_effet for produit in effet.effet_produit.all() for action in produit.produit_action.all())

    def __str__(self):
        return f"Plan d'actions {self.id} : {self.titre}"

class Effet(models.Model):
    id = models.AutoField(primary_key=True)
    plan = models.ForeignKey(PlanAction, related_name="plan_effet", on_delete=models.CASCADE)
    titre = models.CharField(max_length=255)
    couts = models.JSONField(default=default)
    nombre_produits = models.PositiveIntegerField(default=0)
    nombre_actions = models.PositiveIntegerField(default=0)
    nombre_activites = models.PositiveIntegerField(default=0)

    def calculer_couts(self):
        """Calcul du coût total de l'effet en additionnant les coûts de ses produits."""
        couts = [0.0] * self.plan.horizon
        for produit in self.effet_produit.all():
            for i, cout in enumerate(produit.couts):
                couts[i] += cout  # Ajout des coûts des produits
        self.couts = couts
        self.save()
        self.plan.calculer_couts()  # Mise à jour des coûts du plan d'action

    def calculer_nombres(self):
        """Calcul du nombre de produits, actions et activités."""
        effet_produit = self.effet_produit.prefetch_related('produit_action__action_activite')
        
        self.nombre_produits = effet_produit.count()
        self.nombre_actions = sum(produit.produit_action.count() for produit in effet_produit)
        self.nombre_activites = sum(action.action_activite.count() for produit in effet_produit for action in produit.produit_action.all())
        self.plan.calculer_nombres()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)        
        self.plan.calculer_nombres()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

        self.plan.calculer_nombres()
        self.plan.calculer_couts()
        self.plan.save()

    def __str__(self):
        return f"Effet {self.id} : {self.titre}"

class Produit(models.Model):
    id = models.AutoField(primary_key=True)
    effet = models.ForeignKey(Effet, related_name="effet_produit", on_delete=models.CASCADE)
    titre = models.CharField(max_length=255)
    couts = models.JSONField(default=default)
    nombre_actions = models.PositiveIntegerField(default=0)
    nombre_activites = models.PositiveIntegerField(default=0)

    def calculer_couts(self):
        """Calcul du coût total du produit en additionnant les coûts de ses actions."""
        couts = [0.0] * self.effet.plan.horizon
        for action in self.produit_action.all():
            for i, cout in enumerate(action.couts):
                couts[i] += cout  # Ajout des coûts des actions
        self.couts = couts
        self.save()
        self.effet.calculer_couts()  # Mise à jour des coûts de l'effet

        
    def calculer_nombres(self):
        """Calcul du nombre d'actions et d'activités."""
        produit_action = self.produit_action.prefetch_related('action_activite')
        self.nombre_actions = produit_action.count()
        self.nombre_activites = sum(action.action_activite.count() for action in produit_action)
        self.effet.calculer_nombres()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self.effet.calculer_nombres()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

        self.effet.calculer_nombres()
        self.effet.calculer_couts()
        self.effet.save()

    def __str__(self):
        return f"Produit {self.id} : {self.titre}"

class Action(models.Model):
    id = models.AutoField(primary_key=True)
    produit = models.ForeignKey(Produit, related_name="produit_action", on_delete=models.CASCADE)
    titre = models.CharField(max_length=255)
    couts = models.JSONField(default=default)
    nombre_activites = models.PositiveIntegerField(default=0)

    def calculer_couts(self):
        """Calcul du coût total de l'action pour chaque année."""
        couts = [0.0] * self.produit.effet.plan.horizon  # Initialisation du tableau de coûts
        for activite in self.action_activite.all():
            print(activite.couts)  # Affichage des coûts de l'activité
            for i, cout in enumerate(activite.couts):
                couts[i] += cout  # Addition des coûts de chaque activité à la liste globale
        self.couts = couts  # Mise à jour des coûts de l'action
        self.save()  # Sauvegarde de l'objet Action
        self.produit.calculer_couts()  # Mise à jour des coûts du produit


    def calculer_nombres(self):
        """Calcul du nombre d'activités."""
        self.nombre_activites = self.action_activite.count()
        self.produit.calculer_nombres()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self.produit.calculer_nombres()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

        self.produit.calculer_nombres()
        self.produit.calculer_couts()
        self.produit.save()

    def __str__(self):
        return f"Action {self.id} : {self.titre}"

# Modèle pour les activités
class Activite(models.Model):
    id = models.AutoField(primary_key=True)
    action = models.ForeignKey(Action, related_name="action_activite", on_delete=models.CASCADE)
    titre = models.CharField(max_length=255)
    type = models.CharField(
        max_length=50, 
        choices=[
            ('reforme', 'Réforme'), 
            ('investissement', 'Investissement'), 
            ('etude', 'Étude'), 
            ('texte', 'Texte'), 
            ('ordinaire', 'Activité ordinaire')
        ]
    )
    indicateur_label = models.CharField(max_length=255)
    indicateur_reference = models.CharField(max_length=255)
    cibles = models.JSONField(default=default)  
    couts = models.JSONField(default=default)  
    point_focal = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False, blank=False, related_name='point_focal_activites')
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='responsable_activites')


    def clean(self):
        horizon = self.action.produit.effet.plan.horizon
        if not self.cibles or not self.couts:
            raise ValidationError("Les champs 'cibles' et 'couts' ne peuvent pas être vides.")
        if len(self.cibles) != horizon or len(self.couts) != horizon:
            raise ValidationError(f"Les listes doivent contenir {horizon} valeurs.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self.action.calculer_nombres()
        self.action.calculer_couts()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)      
        # Mise à jour en cascade
        self.action.calculer_nombres()
        self.action.calculer_couts()
        self.action.save()

    def __str__(self):
        return self.titre