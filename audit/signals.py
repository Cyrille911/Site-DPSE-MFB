from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import AuditLog

User = get_user_model()


def _get_client_ip(request):
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _get_user_agent(request):
    if not request:
        return ''
    return request.META.get('HTTP_USER_AGENT', '')[:500]


def _guess_user(instance):
    for attr in ('last_modified_by', 'uploaded_by', 'generated_by',
                 'point_focal', 'responsable', 'created_by', 'user', 'author'):
        if hasattr(instance, attr):
            user = getattr(instance, attr)
            if user and hasattr(user, 'pk'):
                return user
    return None


@receiver(user_logged_in)
def log_user_logged_in(sender, request, user, **kwargs):
    AuditLog.objects.create(
        user=user,
        action='LOGIN',
        category='auth',
        description=f"Connexion réussie pour {user.email}",
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
        extra_data={'email': user.email, 'username': user.get_username()},
    )


@receiver(user_logged_out)
def log_user_logged_out(sender, request, user, **kwargs):
    AuditLog.objects.create(
        user=user,
        action='LOGOUT',
        category='auth',
        description=f"Déconnexion de {user.email if user else 'inconnu'}",
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
        extra_data={'email': user.email if user else None},
    )


@receiver(user_login_failed)
def log_user_login_failed(sender, request, credentials, **kwargs):
    email = credentials.get('email') if credentials else None
    AuditLog.objects.create(
        action='LOGIN_FAILED',
        category='auth',
        description=f"Échec de connexion pour {email}",
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
        extra_data={'email': email},
    )


EXCLUDED_APPS = {'admin', 'sessions', 'audit', 'contenttypes', 'migrations', 'auth'}
EXCLUDED_MODELS = {('users', 'user')}


@receiver(post_save)
def log_model_save(sender, instance, created, **kwargs):
    if not hasattr(sender, '_meta'):
        return
    app = sender._meta.app_label
    model = sender._meta.model_name
    if app in EXCLUDED_APPS or (app, model) in EXCLUDED_MODELS:
        return
    if isinstance(instance, AuditLog):
        return

    action = 'CREATE' if created else 'UPDATE'
    try:
        ct = ContentType.objects.get_for_model(sender)
    except Exception:
        ct = None

    AuditLog.objects.create(
        user=_guess_user(instance),
        action=action,
        category='data',
        description=f"{action} {sender._meta.label} #{instance.pk}",
        content_type=ct,
        object_id=instance.pk,
        extra_data={'app': app, 'model': model, 'pk': instance.pk},
    )


@receiver(post_delete)
def log_model_delete(sender, instance, **kwargs):
    if not hasattr(sender, '_meta'):
        return
    app = sender._meta.app_label
    model = sender._meta.model_name
    if app in EXCLUDED_APPS or (app, model) in EXCLUDED_MODELS:
        return
    if isinstance(instance, AuditLog):
        return

    try:
        ct = ContentType.objects.get_for_model(sender)
    except Exception:
        ct = None

    AuditLog.objects.create(
        user=_guess_user(instance),
        action='DELETE',
        category='data',
        description=f"DELETE {sender._meta.label} #{instance.pk}",
        content_type=ct,
        object_id=instance.pk,
        extra_data={'app': app, 'model': model, 'pk': instance.pk},
    )
