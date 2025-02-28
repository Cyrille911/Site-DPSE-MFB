from django.db import models
from django.conf import settings
from django.utils import timezone
import os

def news_directory_path(instance, filename):
    return os.path.join('news', 'media', 'profiles', filename)

class News(models.Model):
    headline = models.CharField(max_length=255, verbose_name="Titre de l'actualité")
    content = models.TextField(verbose_name="Contenu")
    image = models.ImageField(upload_to=news_directory_path, blank=True, null=True, verbose_name="Image associée")
    published_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de publication")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")
    is_featured = models.BooleanField(default=False, verbose_name="Actualité en vedette")
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Créateur")
    external_link = models.URLField(blank=True, null=True, verbose_name="Lien externe")
    resume = models.CharField(max_length=500, blank=True, null=True, verbose_name="Résumé")

    def comment_count(self):
        return self.comments.count()

    def save(self, *args, **kwargs):
        # Auto-remplissage du résumé si non fourni : on prend les 200 premiers caractères du contenu
        if not self.resume and self.content:
            self.resume = self.content[:200] + ("..." if len(self.content) > 200 else "")
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Actualité"
        verbose_name_plural = "Actualités"
        ordering = ['-published_at']

    def __str__(self):
        return self.headline

class NewsComment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='news_comments', verbose_name="Commentateur")
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name="comments", verbose_name="Actualité")
    content = models.TextField(verbose_name="Contenu du commentaire")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Date de création")
    
    class Meta:
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
        ordering = ['created_at']

    def __str__(self):
        return f"Commentaire de {self.user} sur {self.news}"
