from core.models import SystemSetting


class RBACMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        user = request.user
        request.permissions_cache = set()

        # =========================
        # LOAD SYSTEM SETTINGS (SAFE)
        # =========================
        settings = SystemSetting.objects.first()
        request.system_settings = settings

        if user.is_authenticated:

            # =========================
            # SUPERADMIN (FULL ACCESS)
            # =========================
            if user.is_superadmin or user.is_superuser:

                request.permissions_cache = {"*"}
                request.session["rbac_permissions"] = ["*"]

            else:

                # =========================
                # ROLE PERMISSIONS (CLEAN)
                # =========================
                if user.role:

                    perms = user.role.permissions.values_list("code", flat=True)

                    perms_list = list(perms)

                    request.permissions_cache = set(perms_list)
                    request.session["rbac_permissions"] = perms_list

                else:
                    # fallback (session cache)
                    cached = request.session.get("rbac_permissions", [])
                    request.permissions_cache = set(cached)

            # =========================
            # FEATURE FLAGS (SYSTEM CONTROL)
            # =========================
            if settings:

                if not getattr(settings, "enable_pos", True):
                    request.permissions_cache.discard("can_access_pos")

                if not getattr(settings, "enable_keg_tracking", True):
                    request.permissions_cache.discard("can_view_inventory")

                if not getattr(settings, "enable_analytics", True):
                    request.permissions_cache.discard("can_view_reports")

        return self.get_response(request)