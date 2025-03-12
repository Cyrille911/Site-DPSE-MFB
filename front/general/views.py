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

@login_required
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


@login_required
def faq_r(request):
    if request.method == "POST":
        question_id = request.POST.get("question_id")
        reponse_text = request.POST.get("reponse")

        try:
            question = Discussion.objects.get(id=question_id)
            question.reponse = reponse_text  # Enregistrer la réponse
            question.auteur_reponse = request.user
            question.date_reponse = now()  # Enregistrer la date de réponse
            question.save()
        except Discussion.DoesNotExist:
            pass  # Gérer le cas où la question n'existe pas

        return redirect("faq_r")  # Recharger la page

    # Récupérer les questions en attente de réponse
    questions_non_repondues = Discussion.objects.filter(reponse__isnull=True).order_by("-date_question")

    return render(request, 'general/faq_r.html', {
        'questions_non_repondues': questions_non_repondues
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
