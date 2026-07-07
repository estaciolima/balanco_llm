from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


ROLE_PERMISSIONS = {
    "admin": [],
    "reviewer": [],
    "viewer": [],
}


class Command(BaseCommand):
    help = "Create baseline role groups used by the application"

    def handle(self, *args, **options):
        for role_name, permission_codenames in ROLE_PERMISSIONS.items():
            group, _ = Group.objects.get_or_create(name=role_name)
            if permission_codenames:
                permissions = Permission.objects.filter(codename__in=permission_codenames)
                group.permissions.set(permissions)
            self.stdout.write(self.style.SUCCESS(f"Ensured role group: {role_name}"))
