from django.core.exceptions import PermissionDenied


def get_active_business(request):
    """
    Returns the active business for the logged-in user.
    Superadmin returns None (global access).
    """

    user = request.user

    if not user.is_authenticated:
        raise PermissionDenied("User not authenticated")

    # 🔥 SUPERADMIN BYPASS
    if getattr(user, "is_superadmin", False):
        return None

    return getattr(user, "business", None)