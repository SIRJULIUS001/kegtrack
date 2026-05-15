from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.db import transaction
from business.models import Business
from accounts.models import User, Role
from core.models import SystemSetting,AuditLog
from accounts.decorators import superadmin_required

# ======================
# PUBLIC LANDING PAGE
# ======================
def index(request):
    return render(request, "index.html")


# ======================
# SUPER ADMIN CHECK (REUSABLE STYLE)
# ======================
def is_superadmin(user):
    return getattr(user, "is_superadmin", False)


# ======================
# BUSINESS LIST
# ======================
@login_required
def business_list(request):

    if not is_superadmin(request.user):
        return HttpResponseForbidden("Only Super Admin allowed")

    # 🔥 IMPORTANT FIX:
    # show ALL businesses (active + inactive) for management
    businesses = Business.objects.all().order_by("-created_at")

    return render(request, "core/superadmin/business_list.html", {
        "businesses": businesses
    })


# ======================
# CREATE BUSINESS + OWNER + ROLE
# ======================
@login_required
def business_create(request):

    if not is_superadmin(request.user):
        return HttpResponseForbidden("Only Super Admin allowed")

    if request.method == "POST":

        try:
            with transaction.atomic():

                # 1. BUSINESS
                business = Business.objects.create(
                    name=request.POST.get("business_name"),
                    business_type=request.POST.get("business_type"),
                    email=request.POST.get("business_email"),
                    phone=request.POST.get("phone"),
                    address=request.POST.get("address"),
                    created_by=request.user
                )

                # 2. ROLE (OWNER)
                owner_role, _ = Role.objects.get_or_create(
                    name="business_admin",
                    business=business
                )

                # 3. OWNER USER
                User.objects.create_user(
                    username=request.POST.get("username"),
                    email=request.POST.get("email"),
                    password=request.POST.get("password"),
                    phone=request.POST.get("owner_phone"),
                    business=business,
                    role=owner_role,
                    is_superadmin=False,
                    is_active_staff=True
                )

                messages.success(request, "Business created successfully")
                return redirect("core:business_list")

        except Exception as e:
            messages.error(request, f"Error creating business: {str(e)}")

    return render(request, "core/superadmin/business_form.html")


# ======================
# EDIT BUSINESS
# ======================
@login_required
def business_edit(request, pk):

    if not is_superadmin(request.user):
        return HttpResponseForbidden("Only Super Admin allowed")

    business = get_object_or_404(Business, pk=pk)

    if request.method == "POST":

        business.name = request.POST.get("business_name")
        business.business_type = request.POST.get("business_type")
        business.email = request.POST.get("business_email")
        business.phone = request.POST.get("phone")
        business.address = request.POST.get("address")

        business.save()

        messages.success(request, "Business updated successfully")
        return redirect("core:business_list")

    return render(request, "core/superadmin/business_form.html", {
        "business": business
    })


# ======================
# TOGGLE BUSINESS STATUS
# ======================
@login_required
def business_toggle(request, pk):

    if not is_superadmin(request.user):
        return HttpResponseForbidden("Only Super Admin allowed")

    business = get_object_or_404(Business, pk=pk)

    business.is_active = not business.is_active
    business.save()

    status = "enabled" if business.is_active else "disabled"
    messages.success(request, f"Business {status}")

    return redirect("core:business_list")



def is_superadmin(user):
    return getattr(user, "is_superadmin", False)

# ======================
# IMPERSONATION (BUSINESS CONTEXT SWITCH)
# ======================



@login_required
def impersonate_business(request, pk):

    # ======================
    # SECURITY CHECK
    # ======================
    if not is_superadmin(request.user):
        return HttpResponseForbidden("Not allowed")

    business = get_object_or_404(Business, pk=pk)

    # ======================
    # SET IMPERSONATION CONTEXT
    # ======================
    request.session["active_business_id"] = business.id
    request.session["is_impersonating"] = True
    request.session["original_superadmin_id"] = request.user.id

    # OPTIONAL: clear any old cached state
    request.session.modified = True

    messages.success(request, f"Now operating in {business.name}")

    # IMPORTANT: go to business dashboard (not superadmin)
    return redirect("business:home")

@login_required
def exit_impersonation(request):

    # Clean all impersonation state
    request.session.pop("active_business_id", None)
    request.session.pop("is_impersonating", None)
    request.session.pop("original_superadmin_id", None)

    request.session.modified = True

    messages.info(request, "Exited business context")

    return redirect("dashboard:superadmin_home")

def business_context(request):

    return {
        "active_business_id": request.session.get("active_business_id"),
        "is_impersonating": request.session.get("is_impersonating", False),
    }

@login_required
@superadmin_required
def system_settings_view(request):

    settings, _ = SystemSetting.objects.get_or_create(id=1)

    if request.method == "POST":

        # TEXT / NUMERIC FIELDS
        fields = [
            "default_keg_weight", "beer_density", "volume_unit",
            "max_staff_per_business", "trial_days",
            "session_timeout", "audit_retention_days",
            "system_name", "theme_color"
        ]

        for field in fields:
            if field in request.POST:
                setattr(settings, field, request.POST.get(field))

        # BOOLEAN FIELDS
        bool_fields = [
            "enable_pos", "enable_keg_tracking", "enable_analytics", "enable_whatsapp",
            "allow_self_registration", "auto_disable_inactive",
            "force_password_change", "allow_multi_login", "track_login_meta",
            "lock_system_roles", "force_role_sync",
            "enable_email_notifications", "notify_low_stock",
            "notify_keg_loss", "notify_suspicious_activity",
            "enable_audit_logs"
        ]

        for field in bool_fields:
            setattr(settings, field, field in request.POST)

        settings.audit_log_level = request.POST.get("audit_log_level")

        # FILE UPLOAD
        if request.FILES.get("logo"):
            settings.logo = request.FILES.get("logo")

        settings.save()

        messages.success(request, "System settings updated")
        return redirect("core:system_settings")

    return render(request, "core/system_settings.html", {
        "settings": settings
    })
    
from django.core.paginator import Paginator


@login_required
@superadmin_required
def audit_logs_view(request):

    logs = AuditLog.objects.select_related("user", "business").order_by("-timestamp")

    # =========================
    # FILTERS (SaaS READY)
    # =========================
    user_id = request.GET.get("user")
    action = request.GET.get("action")
    business_id = request.GET.get("business")

    if user_id:
        logs = logs.filter(user_id=user_id)

    if action:
        logs = logs.filter(action__icontains=action)

    if business_id:
        logs = logs.filter(business_id=business_id)

    # =========================
    # PAGINATION (CRITICAL FOR SCALE)
    # =========================
    paginator = Paginator(logs, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "core/audit_logs.html", {
        "logs": page_obj,
    })