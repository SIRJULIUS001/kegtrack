def log_action(user, action, business=None, meta=None):

    try:
        from core.models import AuditLog  # lazy import prevents WSGI circular issues

        AuditLog.objects.create(
            user=user,
            business=business,
            action=action,
            meta=meta or {}
        )

    except Exception:
        # NEVER break request flow because of audit failure
        pass
    
from core.middleware.audit import log_action


class AuditLogMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        response = self.get_response(request)

        user = request.user

        if user.is_authenticated:

            try:
                log_action(
                    user=user,
                    action=f"{request.method} {request.path}",
                    business=getattr(user, "business", None),
                    meta={
                        "ip": request.META.get("REMOTE_ADDR"),
                        "device": request.META.get("HTTP_USER_AGENT", "")[:255],
                        "status_code": response.status_code,
                    }
                )
            except Exception:
                pass

        return response