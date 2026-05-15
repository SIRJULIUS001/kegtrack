from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from accounts.models import User, Role
from business.models import Business


# =========================
# LOGIN VIEW
# =========================
def login_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:

            # =========================
            # RBAC LOGIN CHECK (BEFORE LOGIN)
            # =========================
            if not user.can_login():
                messages.error(request, "This account is inactive or has been deleted.")
                return redirect("accounts:login")

            # =========================
            # LOGIN USER
            # =========================
            login(request, user)

            # =========================
            # TRACK LOGIN INFO
            # =========================
            user.last_login_ip = request.META.get("REMOTE_ADDR")
            user.last_device = request.META.get("HTTP_USER_AGENT", "")[:255]
            user.save(update_fields=["last_login_ip", "last_device"])

            # =========================
            # SUPERADMIN ROUTE
            # =========================
            if user.is_superuser or user.is_superadmin:
                return redirect("dashboard:superadmin_home")

            # =========================
            # BUSINESS USER ROUTE
            # =========================
            if user.business:
                return redirect("business:home")

            # =========================
            # ORPHAN SAFETY
            # =========================
            logout(request)
            messages.error(request, "No business assigned to this account.")
            return redirect("accounts:login")

        messages.error(request, "Invalid username or password.")

    return render(request, "accounts/login.html")


# =========================
# LOGOUT
# =========================
def logout_view(request):
    logout(request)
    return redirect("accounts:login")


# =========================
# PROFILE
# =========================
@login_required
def profile_view(request):
    return render(request, "accounts/profile.html", {
        "user": request.user
    })


# =========================
# REGISTER BUSINESS
# =========================
def register_business_view(request):

    if request.method == "POST":

        # ======================
        # CREATE BUSINESS
        # ======================
        business = Business.objects.create(
            name=request.POST.get("business_name"),
            email=request.POST.get("email"),
            phone=request.POST.get("phone"),
        )

        # ======================
        # CREATE OWNER ROLE (CRITICAL)
        # ======================
        owner_role, _ = Role.objects.get_or_create(
            name=Role.OWNER,
            business=business
        )

        # ======================
        # CREATE OWNER USER
        # ======================
        user = User.objects.create_user(
            username=request.POST.get("username"),
            password=request.POST.get("password"),
            email=request.POST.get("email"),
            phone=request.POST.get("phone"),
            business=business,
            role=owner_role,  # ✅ FIXED
            is_superadmin=False,
            is_active_staff=True,
        )

        messages.success(request, "Business created successfully")
        return redirect("accounts:login")

    return render(request, "accounts/register.html")