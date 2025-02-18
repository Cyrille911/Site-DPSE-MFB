from django.db import models
from django.core.exceptions import ValidationError

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
        """Calcul du coût total du plan pour chaque année."""
        couts = [0] * self.horizon
        for effet in self.plan_effets.prefetch_related('effet_produits__produit_actions__action_activites'):
            for i, cout in enumerate(effet.couts):
                couts[i] += cout
        self.couts = couts

    def calculer_nombres(self):
        """Met à jour le nombre total d'effets, produits, actions et activités."""
        plan_effets = self.plan_effets.prefetch_related(
            'effet_produits__produit_actions__action_activites'
        )
        
        self.nombre_effets = plan_effets.count()
        self.nombre_produits = sum(effet.effet_produits.count() for effet in plan_effets)
        self.nombre_actions = sum(produit.produit_actions.count() for effet in plan_effets for produit in effet.effet_produits.all())
        self.nombre_activites = sum(action.action_activites.count() for effet in plan_effets for produit in effet.effet_produits.all() for action in produit.produit_actions.all())

    def __str__(self):
        return f"Plan d'actions {self.id} : {self.titre}"

class Effet(models.Model):
    id = models.AutoField(primary_key=True)
    plan = models.ForeignKey(PlanAction, related_name="plan_effets", on_delete=models.CASCADE)
    titre = models.CharField(max_length=255)
    couts = models.JSONField(default=default)
    nombre_produits = models.PositiveIntegerField(default=0)
    nombre_actions = models.PositiveIntegerField(default=0)
    nombre_activites = models.PositiveIntegerField(default=0)

    def calculer_couts(self):
        """Calcul du coût total de l'effet pour chaque année."""
        couts = [0] * self.plan.horizon
        for produit in self.effet_produits.prefetch_related('produit_actions__action_activites'):
            for i, cout in enumerate(produit.couts):
                couts[i] += cout
        self.couts = couts
    
    def calculer_nombres(self):
        """Calcul du nombre de produits, actions et activités."""
        effet_produits = self.effet_produits.prefetch_related('produit_actions__action_activites')
        
        self.nombre_produits = effet_produits.count()
        self.nombre_actions = sum(produit.produit_actions.count() for produit in effet_produits)
        self.nombre_activites = sum(action.action_activites.count() for produit in effet_produits for action in produit.produit_actions.all())

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
        self.plan.calculer_nombres()
        self.plan.calculer_couts()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

        self.plan.calculer_nombres()
        self.plan.calculer_couts()
        self.plan.save()

    def __str__(self):
        return f"Effet {self.id} : {self.titre}"

class Produit(models.Model):
    id = models.AutoField(primary_key=True)
    effet = models.ForeignKey(Effet, related_name="effet_produits", on_delete=models.CASCADE)
    titre = models.CharField(max_length=255)
    couts = models.JSONField(default=default)
    nombre_actions = models.PositiveIntegerField(default=0)
    nombre_activites = models.PositiveIntegerField(default=0)

    def calculer_couts(self):
        """Calcul du coût total du produit pour chaque année."""
        couts = [0] * self.effet.plan.horizon
        for action in self.produit_actions.prefetch_related('action_activites'):
            for i, cout in enumerate(action.couts):
                couts[i] += cout
        self.couts = couts
    
    def calculer_nombres(self):
        """Calcul du nombre d'actions et d'activités."""
        produit_actions = self.produit_actions.prefetch_related('action_activites')
        self.nombre_actions = produit_actions.count()
        self.nombre_activites = sum(action.action_activites.count() for action in produit_actions)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

        self.effet.calculer_nombres()
        self.effet.plan.calculer_nombres()

        self.effet.calculer_couts()
        self.effet.plan.calculer_couts()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

        self.effet.calculer_nombres()
        self.effet.calculer_couts()
        self.effet.save()

        self.effet.plan.calculer_nombres()
        self.effet.plan.calculer_couts()
        self.effet.plan.save()

    def __str__(self):
        return f"Produit {self.id} : {self.titre}"

class Action(models.Model):
    id = models.AutoField(primary_key=True)
    produit = models.ForeignKey(Produit, related_name="produit_actions", on_delete=models.CASCADE)
    titre = models.CharField(max_length=255)
    couts = models.JSONField(default=default)
    nombre_activites = models.PositiveIntegerField(default=0)

    def calculer_couts(self):
        """Calcul du coût total de l'action pour chaque année."""
        couts = [0] * self.produit.effet.plan.horizon
        for activite in self.action_activites.all():
            for i, cout in enumerate(activite.couts):
                couts[i] += cout
        self.couts = couts
    
    def calculer_nombres(self):
        """Calcul du nombre d'activités."""
        self.nombre_activites = self.action_activites.count()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

        self.produit.calculer_nombres()
        self.produit.effet.calculer_nombres()
        self.produit.effet.plan.calculer_nombres()

        self.produit.calculer_couts()
        self.produit.effet.calculer_couts()
        self.produit.effet.plan.calculer_couts()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

        self.produit.calculer_nombres()
        self.produit.calculer_couts()
        self.produit.save()

        self.produit.effet.calculer_nombres()
        self.produit.effet.calculer_couts()
        self.produit.effet.save()

        self.produit.effet.plan.calculer_nombres()
        self.produit.effet.plan.calculer_couts()
        self.produit.effet.plan.save()

    def __str__(self):
        return f"Action {self.id} : {self.titre}"

# Modèle pour les activités
class Activite(models.Model):
    id = models.AutoField(primary_key=True)
    action = models.ForeignKey(Action, related_name="action_activites", on_delete=models.CASCADE)
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
        self.action.produit.calculer_nombres()
        self.action.produit.effet.calculer_nombres()
        self.action.produit.effet.plan.calculer_nombres()

        self.action.calculer_couts()
        self.action.produit.calculer_couts()
        self.action.produit.effet.calculer_couts()
        self.action.produit.effet.plan.calculer_couts()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        
        # Mise à jour en cascade
        self.action.calculer_nombres()
        self.action.calculer_couts()
        self.action.save()

        self.action.produit.calculer_nombres()
        self.action.produit.calculer_couts()
        self.action.produit.save()

        self.action.produit.effet.calculer_nombres()
        self.action.produit.effet.calculer_couts()
        self.action.produit.effet.save()

        self.action.produit.effet.plan.calculer_nombres()
        self.action.produit.effet.plan.calculer_couts()
        self.action.produit.effet.plan.save()

    def __str__(self):
        return self.titre