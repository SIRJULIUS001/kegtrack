from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum

from accounts.decorators import superadmin_required

from tracking.models import (
    KegFraudSignal,
    BusinessKegPolicy,
    KegSystemConfig,
    KegSession,
    KegVerification,
    Keg
)

from tracking.services.keg_services import open_keg, record_sale, verify_keg
# =========================
# SYSTEM CONFIG
# =========================
@login_required
@superadmin_required
def keg_system_config_view(request):

    config, _ = KegSystemConfig.objects.get_or_create(id=1)

    if request.method == "POST":

        config.enable_keg_tracking = "enable_keg_tracking" in request.POST
        config.force_verification = "force_verification" in request.POST
        config.require_photo_proof = "require_photo_proof" in request.POST
        config.require_weight_check = "require_weight_check" in request.POST
        config.live_camera_only = "live_camera_only" in request.POST

        try:
            config.variance_threshold_percent = float(
                request.POST.get("variance_threshold_percent", 2.0)
            )
            config.beer_density = float(
                request.POST.get("beer_density", 1.01)
            )
        except ValueError:
            messages.error(request, "Invalid numeric input.")
            return redirect("tracking:keg_config")

        config.save()

        messages.success(request, "Keg system settings updated successfully.")
        return redirect("tracking:keg_config")

    return render(request, "tracking/superadmin/keg_config.html", {
        "config": config
    })


# =========================
# BUSINESS POLICY
# =========================
@login_required
@superadmin_required
def business_keg_policy_view(request):

    policies = BusinessKegPolicy.objects.select_related("business")

    return render(request, "tracking/superadmin/business_keg_policy.html", {
        "policies": policies
    })


# =========================
# FRAUD MONITOR
# =========================
@login_required
@superadmin_required
def fraud_monitor_view(request):

    signals = KegFraudSignal.objects.select_related("business").order_by("-fraud_score")

    return render(request, "tracking/superadmin/fraud_monitor.html", {
        "signals": signals
    })


# =========================
# KEG DASHBOARD
# =========================
@login_required
@superadmin_required
def keg_dashboard_view(request):

    # =========================
    # KPIs
    # =========================
    active_sessions = KegSession.objects.filter(status="open").count()

    total_consumed = KegSession.objects.aggregate(
        total=Sum("consumed_volume")
    )["total"] or 0

    total_verifications = KegVerification.objects.count()

    fraud_cases = KegFraudSignal.objects.filter(flagged=True).count()

    # =========================
    # RECENT DATA
    # =========================
    recent_sessions = KegSession.objects.select_related(
        "keg", "keg__business"
    ).order_by("-opened_at")[:10]   # ✅ FIXED HERE

    recent_verifications = KegVerification.objects.select_related(
        "keg"
    ).order_by("-created_at")[:10]

    # =========================
    # RESPONSE
    # =========================
    return render(request, "tracking/superadmin/keg_dashboard.html", {
        "active_sessions": active_sessions,
        "total_consumed": total_consumed,
        "total_verifications": total_verifications,
        "fraud_cases": fraud_cases,
        "recent_sessions": recent_sessions,
        "recent_verifications": recent_verifications,
    })
# =========================
# ACTIVE SESSIONS
# =========================
@login_required
@superadmin_required
def active_keg_sessions_view(request):

    sessions = KegSession.objects.select_related(
        "keg", "keg__business", "opened_by"
    ).filter(status="open")

    return render(request, "tracking/superadmin/active_sessions.html", {
        "sessions": sessions
    })


# =========================
# VERIFICATIONS
# =========================
@login_required
@superadmin_required
def keg_verifications_view(request):

    verifications = KegVerification.objects.select_related(
        "keg", "session", "verified_by", "keg__business"
    ).order_by("-created_at")

    return render(request, "tracking/superadmin/keg_verifications.html", {
        "verifications": verifications
    })


# =========================
# TEST FLOW
# =========================
@login_required
@superadmin_required
def test_keg_flow_view(request):

    kegs = Keg.objects.select_related("business", "keg_type")

    if request.method == "POST":

        action = request.POST.get("action")
        keg_id = request.POST.get("keg")

        keg = get_object_or_404(Keg, id=keg_id)

        if action == "open":
            open_keg(keg, request.user)

        elif action == "sell":
            session = KegSession.objects.filter(
                keg=keg,
                status="open"
            ).first()

            if session:
                try:
                    litres = float(request.POST.get("litres", 0))
                except ValueError:
                    litres = 0

                record_sale(session, litres)

        elif action == "verify":
            session = KegSession.objects.filter(
                keg=keg,
                status="open"
            ).first()

            if session:
                try:
                    weight = float(request.POST.get("weight", 0))
                except ValueError:
                    weight = 0

                verify_keg(
                    session=session,
                    user=request.user,
                    measured_weight=weight,
                    photo=request.FILES.get("photo"),
                    trigger="shift_end"
                )

    return render(request, "tracking/superadmin/test_keg.html", {
        "kegs": kegs
    })