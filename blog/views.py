from django.shortcuts import render

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType

# Modules Django
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# Imports spécifiques au projet
from .models import Blog, BlogComment
# Modules externes
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone


## Blog
def blog_list(request):
    blogs = Blog.objects.all()  # Récupérer tous les blogs
    is_member = request.user.role == 'Membre' if request.user.is_authenticated else False
    return render(request, 'blog/blog_list.html', {'blogs': blogs, 'is_member': is_member})

def blog_detail(request, pk):
    """ Affiche les détails d'un blog spécifique avec gestion des commentaires """
    # Récupérer le blog
    blog = get_object_or_404(Blog, pk=pk)

    # Récupérer les commentaires associés à ce blog
    comments = BlogComment.objects.filter(
        blog=blog.pk
    ).order_by('-created_at')

    # Gestion de la soumission d'un commentaire
    if request.method == 'POST':
        content = request.POST.get('comment')
        if content:
            # Créer un commentaire pour le blog
            BlogComment.objects.create(
                user=request.user,
                blog=blog,
                content=content
            )
            messages.success(request, "Votre commentaire a été ajouté avec succès.")
            return redirect('blog_detail', pk=blog.pk)  # Redirection après ajout du commentaire
        else:
            messages.error(request, "Le commentaire ne peut pas être vide.")

    return render(request, 'blog/blog_detail.html', {
        'blog': blog,
        'comments': comments
    })

@login_required(login_url='login')  # Redirection vers la page de connexion si non connecté
def add_blog(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        category = request.POST.get('category')
        content = request.POST.get('content')
        cover_image = request.FILES.get('cover_image')

        # Créer un nouvel article
        Blog.objects.create(
            title=title,
            category=category,
            content=content,
            cover_image=cover_image,
            author=request.user,
            is_published=False  # Article non publié initialement
        )
        
        messages.success(request, "L'article a été créé avec succès.")
        return redirect('blog_list')  # Rediriger vers la liste des blogs après la création

    return render(request, 'blog/add_blog.html')

@login_required(login_url='login')  # Redirection vers la page de connexion si non connecté
def edit_blog(request, pk):
    blog = get_object_or_404(Blog, pk=pk, author=request.user)

    if request.method == 'POST':
        title = request.POST.get('title')
        category = request.POST.get('category')
        content = request.POST.get('content')
        cover_image = request.FILES.get('cover_image')

        # Mettre à jour l'article existant
        blog.title = title
        blog.category = category
        blog.content = content
        if cover_image:
            blog.cover_image = cover_image
        blog.save()

        messages.success(request, "L'article a été mis à jour avec succès.")
        return redirect('blog_list')  # Rediriger vers la liste des blogs après la mise à jour

    return render(request, 'blog/edit_blog.html', {
        'blog': blog
    })

@login_required
def delete_blog(request, pk):
    blog = get_object_or_404(Blog, pk=pk)
    if blog.author != request.user:
        return HttpResponseForbidden("Vous n'avez pas l'autorisation de supprimer cet article.")
    blog.delete()
    return redirect(reverse('blog_list'))

@login_required
def add_blogcomment(request, pk):
    if request.method == "POST":
        content = request.POST.get("comment", "").strip()

        blog = get_object_or_404(Blog, id=pk)

        BlogComment.objects.create(
            user=request.user,
            blog=blog,
            content=content,
            created_at=timezone.now(),
        )

        messages.success(request, "Votre commentaire a été ajouté avec succès !")
        redirect('news_detail', pk=pk)  # Redirection vers la page précédente
    
    return redirect('news_detail', pk=pk)

def edit_blogcomment(request, pk):
    """
    Permet de modifier un commentaire existant sur la même page.
    """
    # Récupérer le commentaire à partir de son ID
    comment = get_object_or_404(BlogComment, pk=pk)

    if request.method == 'POST':
        # Mettre à jour le contenu du commentaire
        comment.content = request.POST.get('comment')
        comment.save()

        messages.success(request, "Votre commentaire a été mis à jour avec succès.")
            
        return redirect('blog_detail', pk=comment.blog.pk)

def delete_blogcomment(request, pk):
    """
    Vue pour supprimer un commentaire de manière générique.
    """
    # Récupérer le commentaire à partir de l'ID
    comment = get_object_or_404(BlogComment, pk=pk)

    if request.method == "POST":
        # Récupérer l'URL de redirection avant de supprimer le commentaire
        blog = comment.blog

        # Supprimer le commentaire
        comment.delete()
        messages.success(request, "Votre commentaire a été supprimé avec succès.")
        return redirect('blog_detail', pk=blog.pk)

    # Si la méthode n'est pas POST, rediriger vers la page de l'objet associé
    return redirect('blog_detail', pk=blog.pk)
