from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


# =========================
# INTERNAL AUTH CHECK
# =========================
def _auth(user):
    return user.is_authenticated


# =========================
# SUPERADMIN ONLY
# =========================
def superadmin_required(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        user = request.user

        if not _auth(user):
            return redirect("accounts:login")

        if not (user.is_superuser or getattr(user, "is_superadmin", False)):
            return redirect("dashboard:unauthorized")

        return view_func(request, *args, **kwargs)

    return wrapper


# =========================
# RBAC PERMISSION DECORATOR
# =========================
def permission_required(permission_code):

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            user = request.user

            if not _auth(user):
                return redirect("accounts:login")

            # GLOBAL BYPASS
            if user.is_superuser or getattr(user, "is_superadmin", False):
                return view_func(request, *args, **kwargs)

            if not user.has_permission(permission_code):
                messages.error(request, "Access denied: insufficient permissions.")
                return redirect("dashboard:unauthorized")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


# =========================
# BUSINESS SCOPE GUARD
# =========================
def business_required(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        user = request.user

        if not _auth(user):
            return redirect("accounts:login")

        if user.is_superuser or getattr(user, "is_superadmin", False):
            return view_func(request, *args, **kwargs)

        if not user.business:
            messages.error(request, "No business assigned.")
            return redirect("accounts:login")

        return view_func(request, *args, **kwargs)

    return wrapper