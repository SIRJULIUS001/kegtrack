from django.core.management.base import BaseCommand
from accounts.models import Role, Permission


class Command(BaseCommand):
    help = "Seed RBAC system (permissions + roles)"

    def handle(self, *args, **kwargs):

        # =========================
        # 1. PERMISSIONS (GLOBAL)
        # =========================
        permissions = [
            ("can_view_inventory", "View Inventory"),
            ("can_adjust_stock", "Adjust Stock"),
            ("can_manage_products", "Manage Products"),
            ("can_manage_staff", "Manage Staff"),
            ("can_view_reports", "View Reports"),
            ("can_access_pos", "Access POS"),
        ]

        permission_map = {}

        for code, name in permissions:
            perm, _ = Permission.objects.get_or_create(
                code=code,
                defaults={"name": name}
            )
            permission_map[code] = perm

        self.stdout.write(self.style.SUCCESS("Permissions seeded"))

        # =========================
        # 2. ROLE TEMPLATES (GLOBAL DEFAULTS)
        # =========================
        roles_data = [
            {
                "name": Role.OWNER,
                "permissions": [
                    "can_view_inventory",
                    "can_adjust_stock",
                    "can_manage_products",
                    "can_manage_staff",
                    "can_view_reports",
                    "can_access_pos",
                ]
            },
            {
                "name": Role.MANAGER,
                "permissions": [
                    "can_view_inventory",
                    "can_adjust_stock",
                    "can_view_reports",
                    "can_access_pos",
                ]
            },
            {
                "name": Role.STAFF,
                "permissions": [
                    "can_access_pos",
                ]
            },
        ]

        for role_data in roles_data:

            role, _ = Role.objects.get_or_create(
                name=role_data["name"],
                business=None  # template role (used for cloning later per business)
            )

            # 🔥 IMPORTANT: prevent duplication on re-run
            role.permissions.clear()

            for perm_code in role_data["permissions"]:
                role.permissions.add(permission_map[perm_code])

            role.save()

        self.stdout.write(self.style.SUCCESS("Roles seeded"))

        # =========================
        # DONE
        # =========================
        self.stdout.write(
            self.style.SUCCESS("RBAC SYSTEM READY 🚀")
        )