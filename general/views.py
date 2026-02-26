# Modules externes
from django.shortcuts import render

from django.shortcuts import render, redirect
from .models import Discussion
from django.contrib.auth.decorators import login_required

# Page de la discussion (incluant la réponse)
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from .models import Discussion


def faq(request):
    if request.method == "POST":
        nouvelle_question = request.POST.get("question")
        if nouvelle_question:
            Discussion.objects.create(
                question=nouvelle_question,
                auteur_question=request.user
            )
            return redirect("faq")  # Rafraîchir la page après envoi

    # Récupérer toutes les discussions
    questions_non_repondues = Discussion.objects.filter(reponse__isnull=True).order_by("-date_question")
    questions_repondues = Discussion.objects.filter(reponse__isnull=False).order_by("-date_reponse")

    return render(request, 'general/faq.html', {
        'questions_non_repondues': questions_non_repondues,
        'questions_repondues': questions_repondues
    })

## Présentation MFB
def mfb_presentation(request):
    return render(request, 'general/mfb_presentation.html', {})

## Structures
def mfb_structures(request):
    return render(request, 'general/mfb_structures.html', {})

## Accueil
def accueil(request):
    return render(request, 'general/accueil.html', {})

## Glossaire
def glossaire(request):
    return render(request, 'general/glossaire.html', {})

def ministre(request):
    return render(request, 'general/ministre.html', {})
