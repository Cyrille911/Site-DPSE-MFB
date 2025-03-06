from django.db import models
from django.conf import settings
import os

# Modèle d'utilisateur personnalisé
from django.db import models

# Modèle pour les documents
import os
import uuid
from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator


def document_directory_path_mfb(instance, filename):
    
    return os.path.join('documents', 'files', 'mfb', filename)

def cover_directory_path_mfb(instance, filename):
    return os.path.join('documents', 'files', 'mfb', 'covers', filename)

class Document_mfb(models.Model):
    name = models.CharField(max_length=255)
    structure = models.CharField(max_length=255)
    description = models.TextField()
    pans = models.TextField()
    results = models.TextField()  # Principaux résultats du document
    file = models.FileField(upload_to=document_directory_path_mfb)
    uid = models.CharField(max_length=36, unique=True, editable=False, blank=True)  # Utilisation de UUID
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents_mfb')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
        # Nouveau champ pour l'image de couverture
    cover = models.ImageField(
        upload_to=cover_directory_path_mfb,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])
        ],
        blank=True,
        null=True,
        verbose_name="Image de couverture"
    )

    def save(self, *args, **kwargs):
        if not self.uid:
            self.uid = str(uuid.uuid4())[:10]  # Génération d'un UID unique

        # Renommer le fichier en fonction du nom et de l'UID
        if self.file:
            file_extension = os.path.splitext(self.file.name)[1]
            sanitized_name = self.name.replace(' ', '_')
            new_file_name = f"{sanitized_name}_{self.uid}{file_extension}"
            self.file.name = new_file_name

        super(Document_mfb, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (UID: {self.uid})"
    

def document_directory_path_dpse_planification(instance, filename):
    
    return os.path.join('documents', 'files', 'dpse_planification', filename)

def cover_directory_path_dpse_planification(instance, filename):
    return os.path.join('documents', 'files', 'dpse_planification', 'covers', filename)


class Document_dpse_planification(models.Model):
    name = models.CharField(max_length=255)
    structure = models.CharField(max_length=255)
    description = models.TextField()
    pans = models.TextField()
    results = models.TextField()  # Principaux résultats du document
    file = models.FileField(upload_to=document_directory_path_dpse_planification)
    uid = models.CharField(max_length=36, unique=True, editable=False, blank=True)  # Utilisation de UUID
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents_dpse_planification')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
            # Nouveau champ pour l'image de couverture
    cover = models.ImageField(
        upload_to=cover_directory_path_dpse_planification,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])
        ],
        blank=True,
        null=True,
        verbose_name="Image de couverture"
    )


    def save(self, *args, **kwargs):
        if not self.uid:
            self.uid = str(uuid.uuid4())[:10]  # Génération d'un UID unique

        # Renommer le fichier en fonction du nom et de l'UID
        if self.file:
            file_extension = os.path.splitext(self.file.name)[1]
            sanitized_name = self.name.replace(' ', '_')
            new_file_name = f"{sanitized_name}_{self.uid}{file_extension}"
            self.file.name = new_file_name

        super(Document_dpse_planification, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (UID: {self.uid})"
    

def document_directory_path_dpse_suivi_evaluation(instance, filename):
    
    return os.path.join('documents', 'files', 'dpse_suivi_evaluation', filename)

def cover_directory_path_dpse_suivi_evaluation(instance, filename):
    return os.path.join('documents', 'files', 'dpse_suivi_evaluation', 'covers', filename)

class Document_dpse_suivi_evaluation(models.Model):
    name = models.CharField(max_length=255)
    structure = models.CharField(max_length=255)
    description = models.TextField()
    pans = models.TextField()
    results = models.TextField()  # Principaux résultats du document
    file = models.FileField(upload_to=document_directory_path_dpse_suivi_evaluation)
    uid = models.CharField(max_length=36, unique=True, editable=False, blank=True)  # Utilisation de UUID
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents_dpse_suivi_evaluation')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
        # Nouveau champ pour l'image de couverture
    cover = models.ImageField(
        upload_to=cover_directory_path_dpse_suivi_evaluation,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])
        ],
        blank=True,
        null=True,
        verbose_name="Image de couverture"
    )


    def save(self, *args, **kwargs):
        if not self.uid:
            self.uid = str(uuid.uuid4())[:10]  # Génération d'un UID unique

        # Renommer le fichier en fonction du nom et de l'UID
        if self.file:
            file_extension = os.path.splitext(self.file.name)[1]
            sanitized_name = self.name.replace(' ', '_')
            new_file_name = f"{sanitized_name}_{self.uid}{file_extension}"
            self.file.name = new_file_name

        super(Document_dpse_suivi_evaluation, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (UID: {self.uid})"
    

def document_directory_path_dpse_statistiques(instance, filename):
    return os.path.join('documents', 'files', 'dpse_statistiques', filename)

def cover_directory_path_dpse_statistiques(instance, filename):
    return os.path.join('documents', 'files', 'dpse_statistiques', 'covers', filename)

class Document_dpse_statistiques(models.Model):
    name = models.CharField(max_length=255)
    structure = models.CharField(max_length=255)
    description = models.TextField()
    pans = models.TextField()
    results = models.TextField()  # Principaux résultats du document
    file = models.FileField(upload_to=document_directory_path_dpse_statistiques)
    uid = models.CharField(max_length=36, unique=True, editable=False, blank=True)  # Utilisation de UUID
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents_dpse_statistiques')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
        # Nouveau champ pour l'image de couverture
    cover = models.ImageField(
        upload_to=cover_directory_path_dpse_statistiques,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])
        ],
        blank=True,
        null=True,
        verbose_name="Image de couverture"
    )


    def save(self, *args, **kwargs):
        if not self.uid:
            self.uid = str(uuid.uuid4())[:10]  # Génération d'un UID unique

        # Renommer le fichier en fonction du nom et de l'UID
        if self.file:
            file_extension = os.path.splitext(self.file.name)[1]
            sanitized_name = self.name.replace(' ', '_')
            new_file_name = f"{sanitized_name}_{self.uid}{file_extension}"
            self.file.name = new_file_name

        super(Document_dpse_statistiques, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (UID: {self.uid})"
    

def document_directory_path_dpse_qualite(instance, filename):
    
    return os.path.join('documents', 'files', 'dpse_qualite', filename)

def cover_directory_path_dpse_qualite(instance, filename):
    return os.path.join('documents', 'files', 'dpse_qualite', 'covers', filename)

class Document_dpse_qualite(models.Model):
    name = models.CharField(max_length=255)
    structure = models.CharField(max_length=255)
    description = models.TextField()
    pans = models.TextField()
    results = models.TextField()  # Principaux résultats du document
    file = models.FileField(upload_to=document_directory_path_dpse_qualite)
    uid = models.CharField(max_length=36, unique=True, editable=False, blank=True)  # Utilisation de UUID
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents_dpse_qualite')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
            # Nouveau champ pour l'image de couverture
    cover = models.ImageField(
        upload_to=cover_directory_path_dpse_qualite,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])
        ],
        blank=True,
        null=True,
        verbose_name="Image de couverture"
    )


    def save(self, *args, **kwargs):
        if not self.uid:
            self.uid = str(uuid.uuid4())[:10]  # Génération d'un UID unique

        # Renommer le fichier en fonction du nom et de l'UID
        if self.file:
            file_extension = os.path.splitext(self.file.name)[1]
            sanitized_name = self.name.replace(' ', '_')
            new_file_name = f"{sanitized_name}_{self.uid}{file_extension}"
            self.file.name = new_file_name

        super(Document_dpse_qualite, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (UID: {self.uid})"
    

def document_directory_path_dpse_archives(instance, filename):
    
    return os.path.join('documents', 'files', 'dpse_archives', filename)

def cover_directory_path_dpse_archives(instance, filename):
    return os.path.join('documents', 'files', 'dpse_archives', 'covers', filename)

class Document_dpse_archives(models.Model):
    name = models.CharField(max_length=255)
    structure = models.CharField(max_length=255)
    description = models.TextField()
    pans = models.TextField()
    results = models.TextField()  # Principaux résultats du document
    file = models.FileField(upload_to=document_directory_path_dpse_archives)
    uid = models.CharField(max_length=36, unique=True, editable=False, blank=True)  # Utilisation de UUID
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents_dpse_archives')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
        # Nouveau champ pour l'image de couverture
    cover = models.ImageField(
        upload_to=cover_directory_path_dpse_archives,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])
        ],
        blank=True,
        null=True,
        verbose_name="Image de couverture"
    )


    def save(self, *args, **kwargs):
        if not self.uid:
            self.uid = str(uuid.uuid4())[:10]  # Génération d'un UID unique

        # Renommer le fichier en fonction du nom et de l'UID
        if self.file:
            file_extension = os.path.splitext(self.file.name)[1]
            sanitized_name = self.name.replace(' ', '_')
            new_file_name = f"{sanitized_name}_{self.uid}{file_extension}"
            self.file.name = new_file_name

        super(Document_dpse_archives, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (UID: {self.uid})"