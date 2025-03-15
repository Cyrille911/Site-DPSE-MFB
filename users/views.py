# Modules externes
import os
import zipfile
from docx import Document as DocxDocument

from django.shortcuts import render
import plotly.express as px
import plotly.io as pio

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType

# Modules Django
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.utils.html import strip_tags
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings

# Imports spécifiques au projet
from .forms import ConnexionForm, InscriptionMembreForm, InscriptionVisiteurForm, ProfileUpdateForm
from .models import User
from .tokens import account_activation_token

## Personnes (Membres, Visiteurs)
def inscription_membre(request):
    context = {'message': "Bienvenue sur la page d'inscription pour les membres !",
               'title': "Inscription Membre"}
    form = InscriptionMembreForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        
        # Récupérer le rôle depuis le formulaire (si présent) ou définir par défaut
        role = form.cleaned_data.get('role')  # 'membre' par défaut si pas de champ 'role'
        
        # Sauvegarder l'utilisateur avec le rôle
        user.role = role
        user.is_active = False  # Désactiver le compte jusqu'à confirmation par email
        user.save()

        # Assigner les groupes en fonction du rôle
        membre_group, _ = Group.objects.get_or_create(name='Membre')
        user.groups.add(membre_group)  # Tous les membres appartiennent à 'Membre'

        if role == 'point_focal':
            point_focal_group, _ = Group.objects.get_or_create(name='PointFocal')
            user.groups.add(point_focal_group)
        elif role == 'responsable':
            responsable_group, _ = Group.objects.get_or_create(name='Responsable')
            user.groups.add(responsable_group)
        elif role == 'cabinet':
            cabinet_group, _ = Group.objects.get_or_create(name='Cabinet')
            user.groups.add(cabinet_group)

        # Envoyer un email de confirmation
        current_site = get_current_site(request)
        subject = 'Confirmez votre inscription'
        message = render_to_string('users/email_activation_membre.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
        })
        plain_message = strip_tags(message)
        send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, [user.email], html_message=message)

        messages.success(request, 'Un email de confirmation vous a été envoyé.')
        return redirect('connexion_membre')  # Redirection après succès

    context['form'] = form
    return render(request, 'users/formulaire.html', context)

def inscription_visiteur(request):
    context = {'message': "Bienvenue sur la page d'inscription pour les visiteurs !",
               'title': "Inscription Visiteur"}
    form = InscriptionVisiteurForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        
        # Définir le rôle comme 'visiteur'
        user.role = 'visiteur'
        user.is_active = False  # Désactiver le compte jusqu'à confirmation par email
        user.save()

        # Assigner au groupe 'Visiteurs'
        visiteur_group, _ = Group.objects.get_or_create(name='Visiteur')
        user.groups.add(visiteur_group)

        # Envoyer un email de confirmation
        current_site = get_current_site(request)
        subject = 'Confirmez votre inscription'
        message = render_to_string('users/email_activation_visiteur.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
        })
        plain_message = strip_tags(message)
        send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, [user.email], html_message=message)

        messages.success(request, 'Un email de confirmation vous a été envoyé.')
        return redirect('connexion_visiteur')  # Redirection après succès

    context['form'] = form
    return render(request, 'users/formulaire.html', context)

def activer_compte_membre(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        # Mail de demande de confirmation
        current_site = get_current_site(request)
        subject = 'Demande d\'activation de compte'
        message = render_to_string('users/demande_activation.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
        })
        plain_message = strip_tags(message)
        send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, ['cyrilletaha00@gmail.com'], html_message=message)

        messages.success(request, 'Une demande d\'activation a été envoyée pour vérification.')
        return redirect('accueil')  # Rediriger selon le type de connexion
    else:
        if user is not None:
            user.delete()  # Supprimer l'utilisateur si le lien a expiré
            messages.error(request, 'Le lien d\'activation a expiré, votre compte a été supprimé.')
        else:
            messages.error(request, 'Le lien d\'activation est invalide.')
        return redirect('inscription_membre')

def activer_nouveau_membre(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True  # Activer le compte
        user.save()

        # Préparer l'e-mail pour l'utilisateur
        current_site = get_current_site(request)
        subject = 'Votre compte a été activé'
        message = render_to_string('users/confirmation_activation.html', {'user': user, 'domain': current_site.domain,})

        # Envoyer l'e-mail
        plain_message = strip_tags(message)
        send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, [user.email], html_message=message)

        messages.success(request, 'Le compte a été activé avec succès et un e-mail a été envoyé à l\'utilisateur.')
        return redirect('accueil')  # Remplacez par la page vers laquelle vous voulez rediriger
    else:
        messages.error(request, 'Le lien d\'activation est invalide ou a expiré.')
        return redirect('accueil')  # Remplacez par la page vers laquelle vous voulez rediriger

def activer_compte_visiteur(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True  # Activer le compte
        user.save()
        messages.success(request, 'Votre compte a été activé avec succès !')
        return redirect('connexion_visiteur')  # Rediriger selon le type de connexion
    else:
        if user is not None:
            user.delete()  # Supprimer l'utilisateur si le lien a expiré
            messages.error(request, 'Le lien d\'activation a expiré, votre compte a été supprimé.')
        else:
            messages.error(request, 'Le lien d\'activation est invalide.')
        return redirect('inscription_visiteur')

def connexion_membre(request):
    context = {'message': "Bienvenue sur la page de connexion pour les membres !"}
    
    if request.method == 'POST':
        form = ConnexionForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Vérifier si l'utilisateur existe d'abord
            try:
                user_exists = User.objects.get(email=email)
                # Si l'utilisateur existe mais n'est pas actif, afficher un message spécifique
                if not user_exists.is_active:
                    # Activer l'utilisateur pour ce test (à supprimer en production)
                    user_exists.is_active = True
                    user_exists.save()
                    messages.warning(request, "Votre compte a été activé automatiquement pour ce test.")
            except User.DoesNotExist:
                pass

            # Authentification avec email/password
            user = authenticate(request, email=email, password=password)
            
            # Si l'authentification échoue, essayer avec username/password
            if user is None:
                user = authenticate(request, username=email, password=password)

            # Vérifier le rôle (avec plus de flexibilité)
            if user is not None:
                # Convertir en minuscules et supprimer le 's' final pour la comparaison
                user_role = user.role.lower().rstrip('s')
                allowed_roles = ['membre', 'responsable', 'point_focal', 'cabinet']
                
                if user_role in allowed_roles or user.role in allowed_roles:
                    login(request, user)
                    messages.success(request, f'Bienvenue, {user.first_name} !')
                    return redirect('accueil')
                else:
                    messages.error(request, f"Vous n'avez pas les autorisations nécessaires. Votre rôle: {user.role}")
            else:
                # Afficher des informations de débogage
                messages.error(request, "Échec d'authentification. Vérifiez votre email et mot de passe.")
                
                # Informations de débogage (à supprimer en production)
                try:
                    debug_user = User.objects.get(email=email)
                    messages.warning(request, f"Débogage: Utilisateur trouvé avec email {email}, rôle: {debug_user.role}, actif: {debug_user.is_active}")
                except User.DoesNotExist:
                    messages.warning(request, f"Débogage: Aucun utilisateur trouvé avec email {email}")
    else:
        form = ConnexionForm()

    context['form'] = form
    return render(request, 'users/formulaire.html', context)

def connexion_visiteur(request):
    context = {'message': "Bienvenue sur la page de connexion pour les visiteurs !"}
    form = ConnexionForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        # Récupérer les données du formulaire
        form = ConnexionForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            # Authentification de l'utilisateur
            user = authenticate(request, username=username, password=password)
            
            if user is not None and request.user.groups.filter(name="Visiteurs").exists():
                login(request, user)
                messages.success(request, f"Bienvenue, {user.first_name} !")
                return redirect('accueil')  # Redirection après connexion
            else:
                messages.error(request, "Adresse email ou mot de passe incorrect.")

    context['form'] = form
    return render(request, 'users/formulaire.html', context)

@login_required
def profil_utilisateur(request):
    context = {
        'utilisateur': request.user,
        'title': "Mon profil"
    }
    
    # Déterminer quels champs afficher en fonction du rôle
    user_role = request.user.role.lower().rstrip('s')
    
    if user_role in ['membre', 'responsable', 'point_focal', 'cabinet']:
        context['is_membre'] = True
    else:
        context['is_visiteur'] = True
        
    return render(request, 'users/profil_utilisateur.html', context)

@login_required
def modifier_profil(request):
    context = {'message': "Modification de votre profil", 'title': "Modifier mon profil"}
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Votre profil a été mis à jour avec succès !")
            return redirect('profil_utilisateur')
        else:
            messages.error(request, "Erreur lors de la mise à jour du profil. Veuillez corriger les erreurs ci-dessous.")
    else:
        form = ProfileUpdateForm(instance=request.user, user=request.user)
    
    context['form'] = form
    return render(request, 'users/formulaire.html', context)

def deconnexion(request):
    """
    Déconnecte l'utilisateur actuel et le redirige vers la page d'accueil.
    """
    logout(request)
    return redirect('accueil')  # Redirige vers la page d'accueil (ou une autre page)

