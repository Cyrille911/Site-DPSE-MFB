from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


class AuditLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='audit_logs',
    )
    action = models.CharField(max_length=100, db_index=True)
    category = models.CharField(max_length=50, default='request')
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    mac_address = models.CharField(
        max_length=17,
        blank=True,
        verbose_name="Adresse MAC",
        help_text="L'adresse MAC n'est pas récupérable via une requête HTTP standard.",
    )
    content_type = models.ForeignKey(
        ContentType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    extra_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Journal d'audit"
        verbose_name_plural = "Journaux d'audit"
        indexes = [
            models.Index(fields=['-timestamp', 'action']),
            models.Index(fields=['ip_address', '-timestamp']),
            models.Index(fields=['category', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.timestamp} | {self.action} | {self.user} | {self.ip_address}"
