from django.conf import settings

from .models import AuditLog


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    return request.META.get('HTTP_USER_AGENT', '')[:500]


EXCLUDED_PATHS = [
    settings.STATIC_URL,
    settings.MEDIA_URL,
    '/favicon.ico',
    '/health/',
    '/admin/audit/auditlog/',
]


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        path = request.path
        for prefix in EXCLUDED_PATHS:
            if path.startswith(prefix):
                return response

        user = request.user if request.user.is_authenticated else None

        action = f"{request.method}_{path.replace('/', '_').strip('_')[:80]}"

        AuditLog.objects.create(
            user=user,
            action=action,
            category='request',
            description=f"{request.method} {request.path} — statut {response.status_code}",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            extra_data={
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "query_string": request.META.get('QUERY_STRING', ''),
            },
        )

        return response
