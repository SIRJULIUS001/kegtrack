# core/middleware/business_context.py

from business.models import Business


class BusinessContextMiddleware:
    """
    Resolves the active business for every request.
    Supports:
    - Superadmin impersonation
    - Normal user business
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        request.business = None  # default

        user = getattr(request, "user", None)

        if user and user.is_authenticated:

            # =========================
            # 1. SUPERADMIN IMPERSONATION
            # =========================
            business_id = request.session.get("active_business_id")

            if business_id:
                request.business = Business.objects.filter(
                    id=business_id,
                    is_active=True
                ).first()

            # =========================
            # 2. NORMAL USER BUSINESS
            # =========================
            elif hasattr(user, "business") and user.business:
                request.business = user.business

        response = self.get_response(request)
        return response
    
class BusinessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.active_business_id = request.session.get("active_business_id")
        request.is_impersonating = request.session.get("is_impersonating", False)
        return self.get_response(request)