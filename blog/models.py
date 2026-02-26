from django.db import models
from django.conf import settings
from django.utils import timezone

import os

def blog_directory_path(instance, filename):
    
    return os.path.join('blog', 'media', 'profiles', filename)

class Blog(models.Model):
    title = models.CharField(max_length=255, verbose_name="Titre")
    category = models.CharField(max_length=100, verbose_name="Catégorie", blank=True, null=True)
    cover_image = models.ImageField(upload_to=blog_directory_path, null=True, blank=True, verbose_name="Image de couverture")
    content = models.TextField(verbose_name="Contenu")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blogs", verbose_name="Auteur")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")
    is_published = models.BooleanField(default=False, verbose_name="Publié")
    
    def comment_count(self):
        return self.comments.count()

    class Meta:
        verbose_name = "Blog"
        verbose_name_plural = "Blogs"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class BlogComment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_comments', verbose_name="Commentateur")
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name="comments", verbose_name="Blog")
    content = models.TextField(verbose_name="Contenu du commentaire")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Date de création")
    
    class Meta:
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
        ordering = ['created_at']

    def __str__(self):
        return f"Commentaire de {self.author} sur {self.blog}"
