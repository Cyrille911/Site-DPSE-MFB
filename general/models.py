from django.db import models
from django.conf import settings

class Discussion(models.Model):
    question = models.TextField()
    auteur_question = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="questions")
    date_question = models.DateTimeField(auto_now_add=True)
    reponse = models.TextField(blank=True, null=True)
    auteur_reponse = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="reponses")
    date_reponse = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.question[:50]}..."