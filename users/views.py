# Modules externes
from django.shortcuts import render

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# Modules Django
from django.shortcuts import render, redirect
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
from .forms import ConnexionForm, InscriptionMembreForm, InscriptionVisiteurForm
from .models import User
from .tokens import account_activation_token

## Comptes membres
def inscription_membre(request):
    context = {'message': "Bienvenue sur la page d'inscription pour les membres !"}
    form = InscriptionMembreForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.role = 'membre'
        user.is_active = False
        user.save()

        # Ajouter l'utilisateur au groupe Membres
        group, _ = Group.objects.get_or_create(name='Membres')
        user.groups.add(group)  # Ajout explicite au groupe

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
        return redirect('connexion_membre')

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

def connexion_membre(request):
    context = {'message': "Bienvenue sur la page de connexion pour les membres !"}
    form = ConnexionForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            email = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            user = authenticate(request, username=email, password=password)
            if user is not None:
                if user.groups.filter(name="Membres").exists():  # Vérifiez sur 'user', pas 'request.user'
                    login(request, user)
                    messages.success(request, f"Bienvenue, {user.first_name} !")
                    return redirect('accueil')
                else:
                    messages.error(request, "Vous n'êtes pas autorisé dans le groupe Membres.")
            else:
                messages.error(request, "Adresse email ou mot de passe incorrect.")

    context['form'] = form
    return render(request, 'users/formulaire.html', context)

## Comptes visiteurs
def inscription_visiteur(request):
    context = {'message': "Bienvenue sur la page d'inscription pour les visiteurs !"}
    form = InscriptionVisiteurForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.role = 'visiteur'
        user.is_active = False
        user.save()

        # Ajouter l'utilisateur au groupe Visiteurs
        group, _ = Group.objects.get_or_create(name='Visiteurs')
        user.groups.add(group)  # Ajout explicite au groupe

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
        return redirect('connexion_visiteur')

    context['form'] = form
    return render(request, 'users/formulaire.html', context)

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

def connexion_visiteur(request):
    context = {'message': "Bienvenue sur la page de connexion pour les visiteurs !"}
    form = ConnexionForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            print(email)
            
            user = authenticate(request, email=email, password=password)
            if user is not None:
                if user.groups.filter(name="Visiteurs").exists():  # Vérifiez sur 'user', pas 'request.user'
                    login(request, user)
                    messages.success(request, f"Bienvenue, {user.first_name} !")
                    return redirect('accueil')
                else:
                    messages.error(request, "Vous n'êtes pas autorisé dans le groupe Visiteurs.")
            else:
                messages.error(request, "Adresse email ou mot de passe incorrect.")
    
    context['form'] = form
    return render(request, 'users/formulaire.html', context)

@login_required
def profil_utilisateur(request):
    utilisateur = request.user
    return render(request, 'users/profil_utilisateur.html', {'utilisateur': utilisateur})

@login_required
def modifier_profil(request):
    utilisateur = request.user
    if request.method == "POST":
        # Gérer la mise à jour du profil
        utilisateur.first_name = request.POST.get('first_name')
        utilisateur.last_name = request.POST.get('last_name')
        utilisateur.email = request.POST.get('email')
        utilisateur.phone_number = request.POST.get('phone_number')
        # Ajouter la logique pour les champs supplémentaires
        utilisateur.save()
        return redirect('profil_utilisateur')
    return render(request, 'users/modifier_profil.html', {'utilisateur': utilisateur})

def deconnexion(request):
    """
    Déconnecte l'utilisateur actuel et le redirige vers la page d'accueil.
    """
    logout(request)
    return redirect('accueil')  # Redirige vers la page d'accueil (ou une autre page)