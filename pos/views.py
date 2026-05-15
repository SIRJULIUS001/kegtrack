from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from accounts.decorators import superadmin_required
from pos.models import POSSession, POSItem, POSTransaction
from pos.services.pos_engine import open_session, process_sale
from django.db.models import Sum, Count
from pos.models import POSSession, POSTransaction

# =========================
# OPEN SESSION
# =========================
@login_required
def open_pos_session_view(request):

    if request.method == "POST":

        open_session(
            business=request.user.business,
            user=request.user
        )

        return redirect("pos:dashboard")

    return render(request, "pos/open_session.html")


# =========================
# CLOSE SESSION
# =========================
@login_required
def close_pos_session_view(request):

    session = POSSession.objects.filter(
        business=request.user.business,
        is_active=True
    ).first()

    if session:
        session.is_active = False
        session.closed_at = timezone.now()
        session.save()

    return redirect("pos:dashboard")


# =========================
# CREATE SALE
# =========================
@login_required
def create_sale_view(request):

    if request.method == "POST":

        item_id = request.POST.get("item")
        quantity = int(request.POST.get("quantity", 1))

        item = get_object_or_404(POSItem, id=item_id)

        session = POSSession.objects.filter(
            business=request.user.business,
            is_active=True
        ).first()

        if session:
            process_sale(session, item, quantity)

    return redirect("pos:dashboard")


# =========================
# BUSINESS POS DASHBOARD
# =========================
@login_required
def pos_dashboard_view(request):

    business = request.user.business

    sessions = POSSession.objects.filter(
        business=business
    ).order_by("-opened_at")

    transactions = POSTransaction.objects.filter(
        business=business
    ).order_by("-created_at")[:50]

    total_revenue = transactions.aggregate(
        total=Sum("total_price")
    )["total"] or 0

    return render(request, "pos/dashboard.html", {
        "sessions": sessions,
        "transactions": transactions,
        "total_revenue": total_revenue
    })


@login_required
@superadmin_required
def superadmin_pos_dashboard(request):

    # =========================
    # SESSIONS
    # =========================
    sessions = POSSession.objects.select_related(
        "business", "opened_by"
    ).order_by("-opened_at")[:50]

    active_sessions = POSSession.objects.filter(is_active=True).count()

    # =========================
    # TRANSACTIONS
    # =========================
    transactions = POSTransaction.objects.select_related(
        "business", "product"
    ).order_by("-created_at")[:100]

    total_revenue = POSTransaction.objects.aggregate(
        total=Sum("total_price")
    )["total"] or 0

    total_transactions = POSTransaction.objects.aggregate(
        count=Count("id")
    )["count"] or 0

    # =========================
    # AVERAGE SALE
    # =========================
    avg_sale = 0
    if total_transactions > 0:
        avg_sale = total_revenue / total_transactions

    # =========================
    # 🔥 REVENUE PER BUSINESS
    # =========================
    revenue_by_business = POSTransaction.objects.values(
        "business__name"
    ).annotate(
        total=Sum("total_price")
    ).order_by("-total")[:10]

    # =========================
    # RESPONSE
    # =========================
    return render(request, "pos/superadmin_dashboard.html", {
        "sessions": sessions,
        "transactions": transactions,
        "total_revenue": total_revenue,
        "total_transactions": total_transactions,
        "avg_sale": avg_sale,
        "active_sessions": active_sessions,
        "revenue_by_business": revenue_by_business,  # ✅ added
    })     
from accounts.services import get_active_business
from inventory.models import (
    LocationPoint,ProductVariant, Product, StockAtLocation
)
from django.http import HttpResponseForbidden, JsonResponse
from decimal import Decimal
from django.db import transaction
@login_required
def pos_terminal(request):

    business = get_active_business(request)

    if not business:
        return HttpResponseForbidden()

    locations = LocationPoint.objects.filter(
        business=business,
        is_active=True,
        is_deleted=False
    )

    return render(request, "pos/business/terminal.html", {
        "locations": locations,
        "location_id": request.GET.get("location"),
    })     
    
@login_required
def product_list(request):

    business = request.user.business

    products = Product.objects.prefetch_related("variants").all()

    return render(request, "pos/partials/product_grid.html", {
        "products": products
    })
@login_required
def search_products(request):

    query = request.GET.get("search", "")

    products = Product.objects.all()

    if query:
        products = products.filter(name__icontains=query)

    return render(request, "pos/partials/product_grid.html", {
        "products": products
    })
@login_required
def add_to_cart(request):

    variant_id = request.POST.get("variant_id")
    location_id = request.session.get("location_id")

    if not variant_id:
        return JsonResponse({"error": "Missing product"}, status=400)

    variant = ProductVariant.objects.get(id=variant_id)

    cart = request.session.get("pos_cart", {})

    key = str(variant_id)

    if key in cart:
        cart[key]["qty"] += 1
    else:
        cart[key] = {
            "name": variant.product.name,
            "volume": variant.volume,
            "qty": 1,
            "price": str(variant.unit_price),
            "type": "unit",  # later: keg/unit/spirit
        }

    cart[key]["total"] = str(
        Decimal(cart[key]["qty"]) * Decimal(cart[key]["price"])
    )

    request.session["pos_cart"] = cart
    request.session.modified = True

    return JsonResponse({
        "success": True,
        "refresh_cart": True
    })
    
@login_required
def cart_partial(request):

    cart = request.session.get("pos_cart", {})

    total = Decimal("0")

    for item in cart.values():
        total += Decimal(item["total"])

    return render(request, "pos/partials/cart.html", {
        "cart": cart,
        "total": total
    })
    
@login_required
def checkout(request):

    cart = request.session.get("pos_cart", {})

    if not cart:
        return JsonResponse({"error": "Cart empty"}, status=400)

    business = request.user.business

    with transaction.atomic():

        for variant_id, item in cart.items():

            variant = ProductVariant.objects.get(id=variant_id)

            POSTransaction.objects.create(
                business=business,
                product=variant.product,
                quantity=item["qty"],
                unit_price=item["price"],
                total_price=item["total"],
            )

    request.session["pos_cart"] = {}
    request.session.modified = True

    return JsonResponse({
        "success": True,
        "refresh_cart": True
    })
    
@login_required
def keg_panel(request):

    business = request.user.business

    kegs = StockAtLocation.objects.filter(
        location__business=business,
        variant__product__category__name__icontains="keg"
    )

    return render(request, "pos/partials/keg_panel.html", {
        "kegs": kegs
    })
    
@login_required
def activity_feed(request):

    logs = POSTransaction.objects.select_related(
        "product"
    ).order_by("-created_at")[:20]

    return render(request, "pos/partials/activity_feed.html", {
        "logs": logs
    })