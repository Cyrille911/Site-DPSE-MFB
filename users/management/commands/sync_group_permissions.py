from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from users.permissions_config import DEFAULT_ROLE_PERMISSIONS

class Command(BaseCommand):
    help = 'Synchronizes user groups with default permissions defined in permissions_config.py'

    def handle(self, *args, **options):
        self.stdout.write("Starting group permissions synchronization...")

        for group_name, codenames in DEFAULT_ROLE_PERMISSIONS.items():
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(f"Created group: {group_name}")
            
            # Find permissions by codename
            # Note: This assumes unique codenames across apps or that we want all matching codenames.
            # Ideally we should match by app_label too if provided, but codenames are usually unique enough per model.
            # permissions_config.py structure is flat list of codenames for roles.
            
            perms_to_add = []
            missing_codenames = []
            
            for codename in codenames:
                try:
                    # Filter by codename. dealing with potential duplicates if any (unlikely for standard django models unless same model name in diff apps)
                    # To be safe, we might want to be more specific, but let's try strict matching first.
                    p = Permission.objects.filter(codename=codename).first()
                    if p:
                        perms_to_add.append(p)
                    else:
                        missing_codenames.append(codename)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error finding permission {codename}: {e}"))

            if perms_to_add:
                group.permissions.set(perms_to_add)
                self.stdout.write(self.style.SUCCESS(f"Updated {group_name} with {len(perms_to_add)} permissions."))
            
            if missing_codenames:
                self.stdout.write(self.style.WARNING(f"Group {group_name}: Could not find permissions: {', '.join(missing_codenames)}"))

        self.stdout.write(self.style.SUCCESS("Synchronization complete."))
