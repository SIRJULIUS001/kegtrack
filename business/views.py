from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from accounts.models import User
from pos.models import POSTransaction, POSSession
from tracking.models import KegSession
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from business.models import Business
from inventory.models import LocationPoint
from business.models import BusinessStaff


@login_required
def business_home(request):

    user = request.user
    business = None

    # =========================
    # BUSINESS RESOLUTION
    # =========================
    if getattr(user, "is_superadmin", False):

        business_id = request.session.get("active_business_id")

        if not business_id:
            return redirect("dashboard:superadmin_home")

        business = Business.objects.filter(
            id=business_id,
            is_active=True
        ).first()

        if not business:
            return redirect("dashboard:superadmin_home")

    else:
        business = getattr(user, "business", None)

        if not business:
            return redirect("accounts:login")

    # =========================
    # ROLE SAFETY CHECK (FIXED)
    # =========================
    if not user.is_superadmin:

        if not user.role:
            return redirect("accounts:login")

        role_code = (user.role.name or "").lower()

        if role_code not in ["owner", "manager", "staff"]:
            return redirect("accounts:login")

    # =========================
    # STAFF METRICS
    # =========================
    staff_count = User.objects.filter(
        business=business,
        is_deleted=False
    ).count()

    owner_count = User.objects.filter(
        business=business,
        role__name__iexact="owner",
        is_deleted=False
    ).count()

    manager_count = User.objects.filter(
        business=business,
        role__name__iexact="manager",
        is_deleted=False
    ).count()

    # =========================
    # POS METRICS
    # =========================
    active_sessions = POSSession.objects.filter(
        business=business,
        is_active=True
    ).count()

    total_revenue = POSTransaction.objects.filter(
        business=business
    ).aggregate(total=Sum("total_price"))["total"] or 0

    # =========================
    # KEG METRICS
    # =========================
    active_kegs = KegSession.objects.filter(
        keg__business=business,
        status="open"
    ).count()

    total_consumed = KegSession.objects.filter(
        keg__business=business
    ).aggregate(total=Sum("consumed_volume"))["total"] or 0

    # =========================
    # RESPONSE
    # =========================
    return render(request, "business/business_home.html", {
        "business": business,
        "user": user,

        # staff
        "staff_count": staff_count,
        "owner_count": owner_count,
        "manager_count": manager_count,

        # pos
        "active_sessions": active_sessions,
        "total_revenue": total_revenue,

        # keg
        "active_kegs": active_kegs,
        "total_consumed": total_consumed,

        "is_impersonating": request.session.get("is_impersonating", False),
    })


@login_required
def business_profile(request):

    user = request.user

    # =========================
    # SUPERADMIN FLOW
    # =========================
    if getattr(user, "is_superadmin", False):

        business_id = request.session.get("active_business_id")

        if not business_id:
            messages.error(request, "Select a business first")
            return redirect("dashboard:superadmin_home")

        business = Business.objects.filter(id=business_id, is_active=True).first()

        if not business:
            messages.error(request, "Invalid business selected")
            return redirect("dashboard:superadmin_home")

    # =========================
    # BUSINESS USER FLOW
    # =========================
    else:

        staff = BusinessStaff.objects.filter(
            user=user,
            is_active=True
        ).select_related("business").first()

        if not staff:
            messages.error(request, "No business assigned")
            return redirect("accounts:login")

        business = staff.business

    # =========================
    # COUNTERS
    # =========================
    counters = LocationPoint.objects.filter(
        business=business,
        type="counter",
        is_active=True
    )

    return render(request, "business/business_profile.html", {
        "business": business,
        "counters": counters
    })
    
    
@login_required
def counter_create(request):

    staff = BusinessStaff.objects.filter(
        user=request.user,
        is_active=True,
        is_deleted=False
    ).select_related("business", "role").first()

    if not staff:
        return HttpResponse(status=403)

    business = staff.business

    if request.method == "POST":

        name = request.POST.get("name", "").strip()

        if not name:
            return HttpResponse("Name required", status=400)

        # prevent duplicates
        if LocationPoint.objects.filter(
            business=business,
            name__iexact=name,
            type="counter",
            is_active=True
        ).exists():
            return HttpResponse("Counter already exists", status=400)

        counter = LocationPoint.objects.create(
            business=business,
            name=name,
            type="counter",
            is_active=True,
            is_deleted=False
        )

        return render(request, "business/partials/counter_row.html", {
            "counter": counter
        })

    return render(request, "business/partials/counter_form.html")

@login_required
def counter_update(request, pk):

    staff = BusinessStaff.objects.filter(
        user=request.user,
        is_active=True
    ).select_related("business", "role").first()

    if not staff:
        return HttpResponse("Forbidden", status=403)

    # 🔐 permission layer (IMPORTANT for SaaS safety)
    if not getattr(staff.role, "can_manage_counters", True):
        return HttpResponse("Forbidden", status=403)

    counter = get_object_or_404(
        LocationPoint,
        pk=pk,
        business=staff.business,
        type="counter"
    )

    # =========================
    # UPDATE (POST)
    # =========================
    if request.method == "POST":

        name = request.POST.get("name", "").strip()

        if not name:
            return HttpResponse("Name required", status=400)

        counter.name = name
        counter.save()

        return render(request, "business/partials/counter_row.html", {
            "counter": counter
        })

    # =========================
    # EDIT FORM (GET)
    # =========================
    response = render(request, "business/partials/counter_form.html", {
        "counter": counter
    })

    # 🔥 HTMX optimization (prevents weird swap issues)
    response["HX-Trigger"] = "counterEditLoaded"

    return response
@login_required
def counter_delete(request, pk):

    staff = BusinessStaff.objects.filter(
        user=request.user,
        is_active=True,
        is_deleted=False
    ).select_related("business", "role").first()

    if not staff:
        return HttpResponse(status=403)

    if not getattr(staff.role, "can_manage_counters", True):
        return HttpResponse("Forbidden", status=403)

    counter = get_object_or_404(
        LocationPoint,
        pk=pk,
        business=staff.business,
        type="counter"
    )

    counter.is_active = False
    counter.is_deleted = True   # 🔥 FIXED
    counter.save()

    return HttpResponse("")  # HTMX removes row