# Modules externes
from django.shortcuts import render


from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from .models import News
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse

# Modules Django
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

# Imports spécifiques au projet
from .models import News, NewsComment

## Actualité
def news_list(request):
    # Récupérer toutes les actualités (vous pouvez aussi filtrer selon un critère si nécessaire)
    news_list  = News.objects.all()

    # Passer les actualités au template
    return render(request, 'news/news_list.html', {'news_list': news_list })
# def news_list(request):
#     # Récupérer toutes les actualités (vous pouvez aussi filtrer selon un critère si nécessaire)
#     news = News.objects.all()

#     # Passer les actualités au template
#     return render(request, 'news/news_list.html', {'news': news})

def news_detail(request, pk):
    """ Affiche les détails d'une actualité spécifique avec gestion des commentaires """
    # Récupérer l'actualité
    news = get_object_or_404(News, pk=pk)

    # Récupérer les commentaires associés à cette actualité
    comments = NewsComment.objects.filter(
        news=news
    ).order_by('-created_at')

    # Gestion de la soumission d'un commentaire
    if request.method == 'POST' and request.user.is_authenticated:
        comment_content = request.POST.get('comment')
        if comment_content:
            # Créer un commentaire pour l'actualité
            NewsComment.objects.create(
                user=request.user,
                object_id=news.id,
                content=comment_content
            )
            messages.success(request, "Votre commentaire a été ajouté avec succès.")
            return redirect('news_detail', pk=news.pk)  # Redirection après ajout du commentaire

    return render(request, 'news/news_detail.html', {'news': news, 'comments': comments})

# Vue pour ajouter une actualité
def add_news(request):
    # if not request.user.has_perm('general.add_news'):
    #     return HttpResponseForbidden("Vous n'avez pas l'autorisation d'ajouter des actualités.")
    
    if request.method == 'POST':
        headline = request.POST.get('headline')
        content = request.POST.get('content')
        image = request.FILES.get('image')
        is_featured = 'is_featured' in request.POST
        external_link = request.POST.get('external_link')
        resume = request.POST.get('resume')  # Récupération du résumé

        if headline and content:
            news = News(
                headline=headline,
                content=content,
                image=image,
                is_featured=is_featured,
                external_link=external_link,
                resume=resume,  # Ajout du résumé
                creator=request.user
            )
            news.save()
            messages.success(request, "L'actualité a été ajoutée avec succès.")
            return redirect('news_list')
        else:
            messages.error(request, "Le titre et le contenu sont obligatoires.")
    
    return render(request, 'news/add_news.html')
# Vue pour modifier une actualité
@login_required
def edit_news(request, pk):
    news = get_object_or_404(News, pk=pk)

    if not request.user == news.creator and not request.user.has_perm('general.change_news'):
        return HttpResponseForbidden("Vous n'avez pas l'autorisation de modifier cette actualité.")
    
    if request.method == 'POST':
        headline = request.POST.get('headline')
        content = request.POST.get('content')
        image = request.FILES.get('image')
        is_featured = 'is_featured' in request.POST
        external_link = request.POST.get('external_link')

        if headline and content:
            news.headline = headline
            news.content = content
            if image:
                news.image = image
            news.is_featured = is_featured
            news.external_link = external_link
            news.save()
            messages.success(request, "L'actualité a été mise à jour avec succès.")
            return redirect('news_detail', pk=news.pk)
        else:
            messages.error(request, "Le titre et le contenu sont obligatoires.")
    
    return render(request, 'news/edit_news.html', {'news': news})

@login_required
def delete_news(request, pk):
    news = get_object_or_404(News, pk=pk)
    if news.author != request.user:
        return HttpResponseForbidden("Vous n'avez pas l'autorisation de supprimer cet article.")
    news.delete()
    return redirect(reverse('news_list'))
    
@login_required
def add_newscomment(request, pk):
    if request.method == "POST":
        content = request.POST.get("comment", "").strip()

        news = get_object_or_404(News, id=pk)

        NewsComment.objects.create(
            user=request.user,
            news=news,
            content=content,
            created_at=timezone.now(),
        )

        messages.success(request, "Votre commentaire a été ajouté avec succès !")
        redirect('news_detail', pk=pk)  # Redirection vers la page précédente
    
    return redirect('news_detail', pk=pk)

def edit_newscomment(request, pk):
    """
    Permet de modifier un commentaire existant sur la même page.
    """
    # Récupérer le commentaire à partir de son ID
    comment = get_object_or_404(NewsComment, pk=pk)

    if request.method == 'POST':
        # Mettre à jour le contenu du commentaire
        comment.content = request.POST.get('comment')
        comment.save()

        messages.success(request, "Votre commentaire a été mis à jour avec succès.")
            
        return redirect('news_detail', pk=comment.news.pk)

def delete_newscomment(request, pk):
    """
    Vue pour supprimer un commentaire de manière générique.
    """
    # Récupérer le commentaire à partir de l'ID
    comment = get_object_or_404(NewsComment, pk=pk)

    if request.method == "POST":
        # Récupérer l'URL de redirection avant de supprimer le commentaire
        news = comment.news

        # Supprimer le commentaire
        comment.delete()
        messages.success(request, "Votre commentaire a été supprimé avec succès.")
        return redirect('news_detail', pk=news.pk)

    # Si la méthode n'est pas POST, rediriger vers la page de l'objet associé
    return redirect(comment.content_object)
