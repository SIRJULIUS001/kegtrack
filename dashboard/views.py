from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect,get_object_or_404
from django.http import HttpResponseForbidden
from accounts.models import Role, Permission
from business.models import Business
from accounts.models import User
from functools import wraps
from django.db.models import Q
from django.contrib import messages


@login_required
def superadmin_home(request):

    # 🔐 ONLY SUPERADMIN ALLOWED
    if not request.user.is_superadmin:
        return HttpResponseForbidden("Access denied")

    # ======================
    # GLOBAL STATS
    # ======================
    total_businesses = Business.objects.count()
    total_users = User.objects.all().count()
    active_users = User.objects.filter(is_active_staff=True, is_deleted=False).count()

    recent_businesses = Business.objects.order_by("-created_at")[:5]
    recent_users = User.objects.order_by("-created_at")[:5]

    return render(request, "dashboard/superadmin.html", {
        "total_businesses": total_businesses,
        "total_users": total_users,
        "active_users": active_users,
        "recent_businesses": recent_businesses,
        "recent_users": recent_users,
    })
    
    
from .decorators import superadmin_required

def superadmin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("accounts:login")

        # SaaS superadmin check (your system)
        if not request.user.is_superadmin:
            return redirect("dashboard:unauthorized")

        return view_func(request, *args, **kwargs)

    return wrapper

@login_required
@superadmin_required
def staff_list(request):

    business_id = request.GET.get("business")
    role_id = request.GET.get("role")
    search = request.GET.get("search")

    # =========================
    # BASE QUERY (SAFE RBAC)
    # =========================
    users = User.objects.select_related("business", "role").exclude(
        is_superuser=True
    ).exclude(
        is_superadmin=True
    )

    # =========================
    # FILTER: BUSINESS
    # =========================
    if business_id:
        users = users.filter(business_id=business_id)

    # =========================
    # FILTER: ROLE
    # =========================
    if role_id:
        users = users.filter(role_id=role_id)

    # =========================
    # SEARCH FILTER
    # =========================
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search)
        )

    # =========================
    # CONTEXT (FIXED)
    # =========================
    context = {
        "users": users,
        "businesses": Business.objects.all(),
        "roles": Role.objects.filter(business__isnull=True),
    }

    return render(request, "dashboard/staff_list.html", context)
@login_required
@superadmin_required
def assign_staff(request):

    if request.method == "POST":

        user_id = request.POST.get("user")
        role_id = request.POST.get("role")
        business_id = request.POST.get("business")

        user = get_object_or_404(User, id=user_id)
        role = get_object_or_404(Role, id=role_id)

        # =========================
        # VALIDATION (CRITICAL RBAC RULE)
        # =========================

        if role.business and str(role.business_id) != str(business_id):
            return redirect("dashboard:staff_list")

        # assign
        user.business_id = business_id
        user.role = role
        user.is_active_staff = True

        user.save()

        return redirect("dashboard:staff_list")

    return redirect("dashboard:staff_list")

@login_required
@superadmin_required
def toggle_staff_status(request, user_id):

    user = get_object_or_404(User, id=user_id)

    user.is_active_staff = not user.is_active_staff
    user.save()

    return redirect("dashboard:staff_list")

def remove_staff(request, user_id):

    if request.method == "POST":

        user = get_object_or_404(User, id=user_id)

        user.business = None
        user.role = None
        user.is_active_staff = False
        user.save()

    return redirect("dashboard:staff_list")

def unauthorized_view(request):
    return render(request, "dashboard/unauthorized.html")

from django.shortcuts import render, get_object_or_404, redirect
from accounts.models import User

def remove_staff_confirm(request, user_id):

    user = get_object_or_404(User, id=user_id)

    return render(request, "dashboard/confirm_remove.html", {
        "user": user
    })
#global dashboard for superadmin to see stats across all businesses
def role_list(request):

    roles = Role.objects.filter(business=None)  # GLOBAL templates

    return render(request, "dashboard/roles/list.html", {
        "roles": roles
    })
    
def role_create(request):

    if request.method == "POST":

        name = request.POST.get("name")

        Role.objects.create(
            name=name,
            business=None
        )

        messages.success(request, "Role created")
        return redirect("dashboard:role_list")

    return render(request, "dashboard/roles/create.html")


def role_edit(request, role_id):

    role = get_object_or_404(Role, id=role_id)

    if request.method == "POST":

        role.name = request.POST.get("name")
        role.save()

        messages.success(request, "Role updated")
        return redirect("dashboard:role_list")

    return render(request, "dashboard/roles/edit.html", {
        "role": role
    })
    

def update_role_permissions(request, role_id):

    role = get_object_or_404(Role, id=role_id)
    permissions = Permission.objects.all()

    if request.method == "POST":

        # =========================
        # GET SELECTED PERMISSIONS
        # =========================
        selected_ids = request.POST.getlist("permissions")

        # =========================
        # OPTIMIZED UPDATE (NO LOOP)
        # =========================
        role.permissions.set(selected_ids)

        messages.success(request, "Permissions updated successfully")
        return redirect("dashboard:role_list")

    return render(request, "dashboard/roles/permissions.html", {
        "role": role,
        "permissions": permissions,
        "selected": set(role.permissions.values_list("id", flat=True))
    })
    
