from django.db import models

# Modèle d'utilisateur personnalisé
from django.contrib.auth.models import AbstractUser
from django.db import models

import os

def user_directory_path(instance, filename):
    
    return os.path.join('users', 'media', 'profiles', filename)

class User(AbstractUser):
    ROLE_CHOICES = (
        ('membre', 'Membre'),
        ('visiteur', 'Visiteur'),
    )

    PROGRAM_CHOICES = [
        ('Programme 1', 'Programme 1'),
        ('Programme 2', 'Programme 2'),
        ('Programme 3', 'Programme 3'),
        ('Programme 4', 'Programme 4'),
        ('Programme 5', 'Programme 5'),
        ('Programme 6', 'Programme 6'),
        ('Programme 7', 'Programme 7'),
    ]

    # Champs communs
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)  # Optionnel si email est principal
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # Aucun autre champ obligatoire pour le superutilisateur

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)  # Rôle de l'utilisateur
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    photo = models.ImageField(upload_to=user_directory_path, blank=True, null=True)
    
    # Champs spécifiques aux membres
    program = models.CharField(max_length=50, blank=True, null=True, choices=PROGRAM_CHOICES)  # Programme de l'utilisateur
    entity = models.CharField(max_length=50, blank=True, null=True)  # Entité à laquelle l'utilisateur appartient
    function = models.CharField(max_length=100, blank=True, null=True)  # Fonction de l'utilisateur

    # Champs spécifiques aux visiteurs
    profession = models.CharField(max_length=100, blank=True, null=True)  # Profession de l'utilisateur
    interest = models.CharField(max_length=100, blank=True, null=True)  # Intérêt à visiter le site

    def save(self, *args, **kwargs):
        # Assigner l'email au username (pour compatibilité)
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"
    