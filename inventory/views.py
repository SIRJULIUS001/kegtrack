from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.http import HttpResponseForbidden

from business.models import Business
from inventory.models import (
    StockAtLocation,
    ProductCategory,
    LocationPoint,
    Product,
    ProductVariant
)
from functools import wraps
from django.http import HttpResponseForbidden
# =========================================
# 🔐 SUPERADMIN DECORATOR
# =========================================

def superadmin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not getattr(request.user, "is_superadmin", False):
            return HttpResponseForbidden("Superadmin only")
        return view_func(request, *args, **kwargs)
    return wrapper

# =========================================
# 🧠 HELPER: RESOLVE ACTIVE BUSINESS
# =========================================
def get_active_business(request):

    if request.user.is_superadmin:
        business_id = request.session.get("active_business_id")

        if not business_id:
            return Business.objects.first()  # SAFE FALLBACK

        return Business.objects.filter(id=business_id).first()

    return getattr(request.user, "business", None)


# =========================================
# 🟢 BUSINESS INVENTORY DASHBOARD
# =========================================
@login_required
def inventory_dashboard(request):

    business = get_active_business(request)

    if not business:
        return redirect("dashboard:superadmin_home")

    # ======================
    # FILTERS
    # ======================
    location_id = request.GET.get("location")
    category_id = request.GET.get("category")
    search = request.GET.get("search")

    # ======================
    # QUERY
    # ======================
    stocks = StockAtLocation.objects.filter(
        location__business=business
    ).select_related(
        "variant__product__category",
        "location"
    )

    if location_id:
        stocks = stocks.filter(location_id=location_id)

    if category_id:
        stocks = stocks.filter(
            variant__product__category_id=category_id
        )

    if search:
        stocks = stocks.filter(
            Q(variant__product__name__icontains=search) |
            Q(variant__product__category__name__icontains=search)
        )

    stocks = stocks.order_by("location__name")

    # ======================
    # CONTEXT
    # ======================
    categories = ProductCategory.objects.all()

    locations = LocationPoint.objects.filter(
        business=business,
        is_active=True
    )

    return render(request, "inventory/inventory_dashboard.html", {
        "business": business,
        "stocks": stocks,
        "categories": categories,
        "locations": locations,
    })


# =========================================
# 🔴 SUPERADMIN CATALOG DASHBOARD
# =========================================
@login_required
@superadmin_required
def catalog_dashboard(request):

    context = {
        "total_products": Product.objects.count(),
        "total_variants": ProductVariant.objects.count(),
        "total_businesses": Business.objects.count(),
        "total_categories": ProductCategory.objects.count(),
    }

    return render(request, "inventory/catalog/dashboard.html", context)


# =========================================
# 🔴 PRODUCT CRUD (GLOBAL)
# =========================================
@login_required
@superadmin_required
def product_list(request):

    products = Product.objects.select_related("category").all()

    return render(request, "inventory/catalog/product_list.html", {
        "products": products
    })


@login_required
@superadmin_required
def product_create(request):

    categories = ProductCategory.objects.all()

    if request.method == "POST":
        name = request.POST.get("name")
        category_id = request.POST.get("category")

        Product.objects.create(
            name=name,
            category_id=category_id
        )

        return redirect("inventory:product_list")

    return render(request, "inventory/catalog/product_form.html", {
        "categories": categories
    })


@login_required
@superadmin_required
def product_update(request, pk):

    product = get_object_or_404(Product, pk=pk)
    categories = ProductCategory.objects.all()

    if request.method == "POST":
        product.name = request.POST.get("name")
        product.category_id = request.POST.get("category")
        product.save()

        return redirect("inventory:product_list")

    return render(request, "inventory/catalog/product_form.html", {
        "product": product,
        "categories": categories
    })


@login_required
@superadmin_required
def product_delete(request, pk):

    product = get_object_or_404(Product, pk=pk)
    product.delete()

    return redirect("inventory:product_list")


# =========================================
# 🔴 PRODUCT VARIANTS (GLOBAL)
# =========================================
@login_required
@superadmin_required
def variant_list(request):

    variants = ProductVariant.objects.select_related("product").all()

    return render(request, "inventory/catalog/variant_list.html", {
        "variants": variants
    })


@login_required
@superadmin_required
def variant_create(request):

    products = Product.objects.all()

    if request.method == "POST":
        product_id = request.POST.get("product")
        volume = request.POST.get("volume")
        price = request.POST.get("price")

        ProductVariant.objects.create(
            product_id=product_id,
            volume=volume,
            unit_price=price
        )

        return redirect("inventory:variant_list")

    return render(request, "inventory/catalog/variant_form.html", {
        "products": products
    })
    
@login_required
@superadmin_required
def variant_update(request, pk):

    variant = get_object_or_404(ProductVariant, pk=pk)
    products = Product.objects.all()

    if request.method == "POST":
        variant.product_id = request.POST.get("product")
        variant.volume = request.POST.get("volume")
        variant.unit_price = request.POST.get("price")
        variant.save()

        return redirect("inventory:variant_list")

    return render(request, "inventory/catalog/variant_form.html", {
        "variant": variant,
        "products": products
    })
    
    

    
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.db.models import Prefetch

from business.models import BusinessStaff,BusinessProductPrice
from inventory.models import LocationPoint, StockAtLocation
from inventory.models import ProductVariant


# =========================
# INVENTORY DASHBOARD
# =========================
def get_user_business(user):
    return BusinessStaff.objects.filter(
        user=user,
        is_active=True
    ).select_related("business").first()



# =========================
# DASHBOARD (MAIN PAGE)
# =========================
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from decimal import Decimal
   
from django.db import transaction
from django.http import JsonResponse  
from .models import StockAtLocation, LocationPoint, StockMovement

@login_required
def business_inventory_dashboard(request):
    staff = get_user_business(request.user)
    if not staff:
        return HttpResponse(status=403)

    business = staff.business
    location_id = request.GET.get("location")

    # =========================
    # LOCATIONS
    # =========================
    locations = LocationPoint.objects.filter(
        business=business,
        is_active=True,
        is_deleted=False
    ).order_by("name")

    # =========================
    # STOCK
    # =========================
    stock_items = StockAtLocation.objects.filter(
        location__business=business
    ).select_related(
        "location",
        "variant__product"
    ).order_by(
        "location__name",
        "variant__product__name"
    )

    if location_id and location_id.isdigit():
        stock_items = stock_items.filter(location_id=location_id)

    # =========================
    # 🔥 PRICE MAP (ADD THIS)
    # =========================
    price_map = {
        p.variant_id: p.price
        for p in BusinessProductPrice.objects.filter(
            business=business,
            is_active=True
        )
    }

    # =========================
    # 🔥 MERGE STOCK + PRICE
    # =========================
    for stock in stock_items:
        stock.price = price_map.get(stock.variant_id, 0)
        stock.available = stock.available_stock()

    # =========================
    # GLOBAL PRODUCT CATALOG
    # =========================
    products = Product.objects.all().select_related(
        "category"
    ).prefetch_related(
        "variants"
    ).order_by("name")

    return render(request, "inventory/business/business_inventory_dashboard.html", {
        "business": business,
        "locations": locations,
        "stock_items": stock_items,
        "products": products,
        "location_id": location_id,
        "price_map": price_map,
    })
@login_required
def add_to_cart(request):
    staff = get_user_business(request.user)
    if not staff:
        return HttpResponseForbidden()

    business = staff.business

    variant_id = request.POST.get("variant_id")

    # =========================
    # LOCATION
    # =========================
    location_id = (
        request.POST.get("location_id")
        or request.session.get("location_id")
    )

    if not location_id or not str(location_id).isdigit():
        return JsonResponse({
            "error": "Select a counter first"
        }, status=400)

    location_id = int(location_id)

    # persist active counter
    request.session["location_id"] = location_id

    # =========================
    # QTY
    # =========================
    try:
        qty = int(request.POST.get("qty", 1))
    except (TypeError, ValueError):
        qty = 1

    if qty <= 0:
        qty = 1

    # =========================
    # VALIDATE VARIANT
    # =========================
    if not variant_id or not str(variant_id).isdigit():
        return JsonResponse({
            "error": "Invalid product variant"
        }, status=400)

    variant = ProductVariant.objects.select_related(
        "product"
    ).filter(
        id=int(variant_id)
    ).first()

    if not variant:
        return JsonResponse({
            "error": "Variant not found"
        }, status=404)

    # =========================
    # EXISTING STOCK (OPTIONAL)
    # =========================
    # Counter setup allows NEW variants
    stock = StockAtLocation.objects.filter(
        location_id=location_id,
        variant=variant
    ).first()

    # use existing price if available
    price = stock.price if stock else Decimal("0")

    # =========================
    # SESSION CART
    # =========================
    cart = request.session.get("pos_cart", {})

    key = str(variant.id)

    if key in cart:

        cart[key]["qty"] += qty

    else:

        cart[key] = {
            "variant_id": variant.id,
            "name": variant.product.name,
            "volume": variant.volume,
            "qty": qty,
            "price": str(price),
        }

    # =========================
    # RECALCULATE TOTAL
    # =========================
    cart[key]["total"] = str(
        Decimal(cart[key]["qty"]) *
        Decimal(cart[key]["price"])
    )

    # =========================
    # SAVE SESSION
    # =========================
    request.session["pos_cart"] = cart
    request.session.modified = True

    return JsonResponse({
        "success": True,
        "message": f"{variant.product.name} added to pending stock",
        "refresh_cart": True,
    })
    


@login_required
def stock_commit(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    staff = get_user_business(request.user)
    if not staff:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    business = staff.business

    location_id = request.POST.get("location_id")

    if not location_id:
        return JsonResponse({"error": "location_id missing"}, status=400)

    try:
        location_id = int(location_id)
    except ValueError:
        return JsonResponse({"error": "Invalid location_id"}, status=400)

    location = LocationPoint.objects.filter(
        id=location_id,
        business=business,
        is_active=True,
        is_deleted=False
    ).first()

    if not location:
        return JsonResponse({"error": "Location not found"}, status=404)

    cart = request.session.get("pos_cart", {})

    if not cart:
        return JsonResponse({"error": "Cart is empty"}, status=400)

    committed_items = 0

    with transaction.atomic():

        for variant_id, item in cart.items():

            if not str(variant_id).isdigit():
                continue

            # READ OVERRIDES
            qty_input = request.POST.get(f"qty_{variant_id}")
            price_input = request.POST.get(f"price_{variant_id}")

            try:
                qty = int(qty_input) if qty_input else int(item["qty"])
                price = Decimal(price_input) if price_input else Decimal(item["price"])
            except (TypeError, ValueError):
                continue

            if qty < 0:
                continue

            variant = ProductVariant.objects.filter(id=int(variant_id)).first()

            if not variant:
                continue

            # UPSERT STOCK (NO DUPLICATES)
            stock, created = StockAtLocation.objects.get_or_create(
                location=location,
                variant=variant,
                defaults={
                    "quantity": qty,
                    "price": price
                }
            )

            if not created:
                stock.quantity += qty
                stock.price = price
                stock.save()

            committed_items += 1

    # CLEAR CART
    request.session["pos_cart"] = {}
    request.session.modified = True

    return JsonResponse({
        "success": True,
        "message": f"{committed_items} items committed successfully",
        "refresh_cart": True,
        "refresh_stock": True,
    })
    
@login_required
def stock_panel(request):
    staff = get_user_business(request.user)
    business = staff.business

    location_id = request.GET.get("location")

    stock_items = StockAtLocation.objects.filter(
        location__business=business
    ).select_related("location", "variant__product")

    if location_id:
        stock_items = stock_items.filter(location_id=location_id)

    return render(request, "inventory/partials/stock_panel.html", {
        "stock_items": stock_items
    })
    
from decimal import Decimal


@login_required
def cart_partial(request):
    staff = get_user_business(request.user)
    if not staff:
        return HttpResponseForbidden()

    cart = request.session.get("pos_cart", {})
    location_id = request.session.get("location_id")

    cart_items = []
    total = Decimal("0")

    for variant_id, item in cart.items():

        try:
            qty = int(item.get("qty", 0))
            price = Decimal(str(item.get("price", 0)))
        except (TypeError, ValueError):
            continue

        subtotal = qty * price
        total += subtotal

        cart_items.append({
            "variant_id": variant_id,
            "name": item.get("name"),
            "volume": item.get("volume"),
            "qty": qty,
            "price": price,
            "total": subtotal,
        })

    return render(request, "inventory/partials/cart_partial.html", {
        "cart_items": cart_items,
        "cart_total": total,
        "location_id": location_id,
    })
    
from django.shortcuts import render
from .models import Product

def product_search(request):
    query = request.GET.get("search", "")
    location_id = request.GET.get("location")

    products = Product.objects.all()

    if query:
        products = products.filter(name__icontains=query)

    context = {
        "products": products,
        "location_id": location_id,
    }

    return render(request, "inventory/partials/product_list.html", context)  
@login_required
def update_stock(request, stock_id):

    stock = get_object_or_404(StockAtLocation, id=stock_id)

    qty = request.POST.get("quantity")
    price = request.POST.get("price")

    if qty is not None:
        try:
            stock.quantity = int(qty)
        except ValueError:
            pass

    if price is not None:
        try:
            stock.price = Decimal(price)
        except:
            pass

    stock.save()

    return HttpResponse(status=204)

    return HttpResponse(status=204)      
@login_required
def delete_stock(request, stock_id):

    stock = get_object_or_404(StockAtLocation, id=stock_id)
    stock.delete()

    return HttpResponse(status=204)