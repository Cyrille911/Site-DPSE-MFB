from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        'timestamp',
        'action',
        'category',
        'user',
        'ip_address',
        'description',
    )
    list_filter = ('action', 'category', 'timestamp')
    search_fields = ('description', 'ip_address', 'user_agent', 'mac_address')
    date_hierarchy = 'timestamp'
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
