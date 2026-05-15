from django.http import HttpResponseForbidden

def superadmin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden("Login required")

        if not getattr(request.user, "is_superadmin", False):
            return HttpResponseForbidden("Superadmin only")

        return view_func(request, *args, **kwargs)

    return wrapper