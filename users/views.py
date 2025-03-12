from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.conf import settings
from .forms import ConnexionForm, InscriptionMembreForm, InscriptionVisiteurForm
from .models import User
from .tokens import account_activation_token

# Page d'accueil (optionnelle, à adapter selon vos besoins)
def accueil(request):
    return render(request, 'users/accueil.html')

# Inscription des membres
def inscription_membre(request):
    context = {'message': "Bienvenue sur la page d'inscription pour les membres !"}
    form = InscriptionMembreForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.role = 'Membres'
        group, _ = Group.objects.get_or_create(name='Membres')
        user.is_active = False  # Désactiver jusqu'à activation
        user.save()
        user.groups.add(group)

        # Envoyer email de confirmation
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

# Connexion des membres
def connexion_membre(request):
    context = {'message': "Bienvenue sur la page de connexion pour les membres !"}
    form = ConnexionForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = authenticate(request, username=email, password=password)

        if user is not None and user.role == "Membres":  # Utilisation de `role` au lieu du groupe
            login(request, user)
            messages.success(request, f"Bienvenue, {user.first_name} !")
            return redirect('accueil')
        else:
            messages.error(request, "Adresse email ou mot de passe incorrect, ou vous n'êtes pas un membre.")

    context['form'] = form
    return render(request, 'users/formulaire.html', context)

# Inscription des visiteurs
def inscription_visiteur(request):
    context = {'message': "Bienvenue sur la page d'inscription pour les visiteurs !"}
    form = InscriptionVisiteurForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.role = 'visiteur'
        group, _ = Group.objects.get_or_create(name='Visiteurs')
        user.is_active = False
        user.save()
        user.groups.add(group)

        # Envoyer email de confirmation
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

# Connexion des visiteurs
def connexion_visiteur(request):
    context = {'message': "Bienvenue sur la page de connexion pour les visiteurs !"}
    form = ConnexionForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        if user is not None and user.groups.filter(name="Visiteurs").exists():
            login(request, user)
            messages.success(request, f"Bienvenue, {user.first_name} !")
            return redirect('accueil')
        else:
            messages.error(request, "Adresse email ou mot de passe incorrect, ou vous n'êtes pas un visiteur.")

    context['form'] = form
    return render(request, 'users/formulaire.html', context)

# Activation du compte membre (première étape)
def activer_compte_membre(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
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
        return redirect('accueil')
    else:
        if user is not None:
            user.delete()
            messages.error(request, 'Le lien d\'activation a expiré, votre compte a été supprimé.')
        else:
            messages.error(request, 'Le lien d\'activation est invalide.')
        return redirect('inscription_membre')

# Activation finale par l'administrateur
def activer_nouveau_membre(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()

        current_site = get_current_site(request)
        subject = 'Votre compte a été activé'
        message = render_to_string('users/confirmation_activation.html', {
            'user': user,
            'domain': current_site.domain,
        })
        plain_message = strip_tags(message)
        send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, [user.email], html_message=message)

        messages.success(request, 'Le compte a été activé avec succès.')
        return redirect('accueil')
    else:
        messages.error(request, 'Le lien d\'activation est invalide ou a expiré.')
        return redirect('accueil')

# Activation du compte visiteur
def activer_compte_visiteur(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Votre compte a été activé avec succès !')
        return redirect('connexion_visiteur')
    else:
        if user is not None:
            user.delete()
            messages.error(request, 'Le lien d\'activation a expiré, votre compte a été supprimé.')
        else:
            messages.error(request, 'Le lien d\'activation est invalide.')
        return redirect('inscription_visiteur')

# Profil utilisateur
@login_required
def profil_utilisateur(request):
    utilisateur = request.user
    return render(request, 'users/profil_utilisateur.html', {'utilisateur': utilisateur})

# Modifier le profil
@login_required
def modifier_profil(request):
    utilisateur = request.user
    if request.method == "POST":
        utilisateur.first_name = request.POST.get('first_name')
        utilisateur.last_name = request.POST.get('last_name')
        utilisateur.email = request.POST.get('email')
        utilisateur.phone_number = request.POST.get('phone_number')
        utilisateur.save()
        return redirect('profil_utilisateur')
    return render(request, 'users/modifier_profil.html', {'utilisateur': utilisateur})

# Déconnexion
def deconnexion(request):
    logout(request)
    return redirect('accueil')