# Modules Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404

# Imports spécifiques au projet
from .models import News, NewsComment


def _peut_gerer_news(user, news, perm):
    return user.is_authenticated and (user == news.creator or user.has_perm(perm))


def _peut_gerer_commentaire(user, comment):
    return user.is_authenticated and (user == comment.user or user.has_perm('news.delete_newscomment'))


## Actualité
def news_list(request):
    news_list = News.objects.select_related('creator').all()
    return render(request, 'news/news_list.html', {'news_list': news_list})


def news_detail(request, pk):
    """Affiche les détails d'une actualité avec ses commentaires."""
    news = get_object_or_404(News.objects.select_related('creator'), pk=pk)
    comments = news.comments.select_related('user').order_by('-created_at')
    return render(request, 'news/news_detail.html', {
        'news': news,
        'comments': comments,
        'peut_modifier': _peut_gerer_news(request.user, news, 'news.change_news'),
        'peut_supprimer': _peut_gerer_news(request.user, news, 'news.delete_news'),
    })


@login_required
def add_news(request):
    """Ajoute une actualité."""
    if request.method == 'POST':
        headline = request.POST.get('headline', '').strip()
        content = request.POST.get('content', '').strip()

        if headline and content:
            News.objects.create(
                headline=headline,
                content=content,
                image=request.FILES.get('image'),
                is_featured='is_featured' in request.POST,
                external_link=request.POST.get('external_link') or None,
                resume=request.POST.get('resume', '').strip() or None,
                creator=request.user,
            )
            messages.success(request, "L'actualité a été ajoutée avec succès.")
            return redirect('news_list')
        messages.error(request, "Le titre et le contenu sont obligatoires.")

    return render(request, 'news/add_news.html')


@login_required
def edit_news(request, pk):
    """Modifie une actualité (créateur ou utilisateur autorisé)."""
    news = get_object_or_404(News, pk=pk)
    if not _peut_gerer_news(request.user, news, 'news.change_news'):
        return HttpResponseForbidden("Vous n'avez pas l'autorisation de modifier cette actualité.")

    if request.method == 'POST':
        headline = request.POST.get('headline', '').strip()
        content = request.POST.get('content', '').strip()

        if headline and content:
            news.headline = headline
            news.content = content
            if request.FILES.get('image'):
                news.image = request.FILES['image']
            news.is_featured = 'is_featured' in request.POST
            news.external_link = request.POST.get('external_link') or None
            news.resume = request.POST.get('resume', '').strip() or None
            news.save()
            messages.success(request, "L'actualité a été mise à jour avec succès.")
            return redirect('news_detail', pk=news.pk)
        messages.error(request, "Le titre et le contenu sont obligatoires.")

    return render(request, 'news/edit_news.html', {'news': news})


@login_required
def delete_news(request, pk):
    """Supprime une actualité (POST uniquement)."""
    news = get_object_or_404(News, pk=pk)
    if not _peut_gerer_news(request.user, news, 'news.delete_news'):
        return HttpResponseForbidden("Vous n'avez pas l'autorisation de supprimer cette actualité.")
    if request.method != 'POST':
        return redirect('news_detail', pk=news.pk)
    news.delete()
    messages.success(request, "L'actualité a été supprimée.")
    return redirect('news_list')


@login_required
def add_newscomment(request, pk):
    news = get_object_or_404(News, pk=pk)
    if request.method == "POST":
        content = request.POST.get("comment", "").strip()
        if content:
            NewsComment.objects.create(user=request.user, news=news, content=content)
            messages.success(request, "Votre commentaire a été ajouté avec succès !")
        else:
            messages.error(request, "Le commentaire ne peut pas être vide.")
    return redirect('news_detail', pk=pk)


@login_required
def edit_newscomment(request, pk):
    """Modifie un commentaire (auteur uniquement)."""
    comment = get_object_or_404(NewsComment, pk=pk)
    if not _peut_gerer_commentaire(request.user, comment):
        return HttpResponseForbidden("Vous n'avez pas l'autorisation de modifier ce commentaire.")

    if request.method == 'POST':
        content = request.POST.get('comment', '').strip()
        if content:
            comment.content = content
            comment.save()
            messages.success(request, "Votre commentaire a été mis à jour avec succès.")
            return redirect('news_detail', pk=comment.news.pk)
        messages.error(request, "Le commentaire ne peut pas être vide.")

    return render(request, 'news/edit_newscomment.html', {'comment': comment})


@login_required
def delete_newscomment(request, pk):
    """Supprime un commentaire (auteur uniquement, POST uniquement)."""
    comment = get_object_or_404(NewsComment, pk=pk)
    news_pk = comment.news.pk
    if not _peut_gerer_commentaire(request.user, comment):
        return HttpResponseForbidden("Vous n'avez pas l'autorisation de supprimer ce commentaire.")
    if request.method == "POST":
        comment.delete()
        messages.success(request, "Votre commentaire a été supprimé avec succès.")
    return redirect('news_detail', pk=news_pk)
