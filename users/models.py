# users/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from django.db.models.signals import post_migrate
from django.dispatch import receiver
import os

def user_directory_path(instance, filename):
    return os.path.join('users', 'media', 'profiles', filename)

class User(AbstractUser):
    ROLE_CHOICES = (
        ('point_focal', 'Point Focal'),
        ('responsable', 'Responsable'),
        ('suiveur_evaluateur', 'Suiveur Evaluateur'),
        ('cabinet', 'Cabinet MFB'),
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
    username = models.CharField(max_length=150, blank=True, null=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    photo = models.ImageField(upload_to=user_directory_path, blank=True, null=True)
    
    # Champs spécifiques aux membres
    program = models.CharField(max_length=50, blank=True, null=True, choices=PROGRAM_CHOICES)
    entity = models.CharField(max_length=50, blank=True, null=True)
    function = models.CharField(max_length=100, blank=True, null=True)

    # Champs spécifiques aux visiteurs
    profession = models.CharField(max_length=100, blank=True, null=True)
    interest = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)
        self.sync_groups()

    def sync_groups(self):
        """Synchronise le champ role avec les groupes correspondants."""
        role_to_group = {
            'point_focal': 'PointFocal',
            'responsable': 'Responsable',
            'suiveur_evaluateur': 'SuiveurEvaluateur',
            'cabinet': 'CabinetMFB',
            'visiteur': 'Visiteur',
        }
        group_name = role_to_group.get(self.role)
        if group_name:
            group, _ = Group.objects.get_or_create(name=group_name)
            if not self.groups.filter(name=group_name).exists():
                self.groups.clear()
                self.groups.add(group)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"

    def has_role(self, role_name):
        return self.groups.filter(name=role_name).exists() or self.role == role_name.lower().replace(' ', '_')

@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    group_names = [
        'PointFocal',
        'Responsable',
        'SuiveurEvaluateur',
        'CabinetMFB',
        'Visiteur',
    ]
    for name in group_names:
        Group.objects.get_or_create(name=name)