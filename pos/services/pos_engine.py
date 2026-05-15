from django.utils import timezone
from pos.models import POSSession, POSTransaction
from tracking.services.keg_engine import consume_keg


# =========================
# OPEN SESSION
# =========================
def open_session(business, user):

    session, created = POSSession.objects.get_or_create(
        business=business,
        is_active=True,
        defaults={
            "opened_by": user,
        }
    )

    return session


# =========================
# PROCESS SALE (FINAL)
# =========================
def process_sale(session, pos_item, quantity=1):

    total_price = pos_item.price * quantity

    transaction = POSTransaction.objects.create(
        session=session,
        business=session.business,
        product=pos_item.product,   # ✅ correct link
        quantity=quantity,
        unit_price=pos_item.price,
        total_price=total_price
    )

    # =========================
    # INVENTORY + KEG HANDLING
    # =========================
    handle_inventory(pos_item, quantity, session.business)

    return transaction


# =========================
# INVENTORY HANDLER (SINGLE SOURCE OF TRUTH)
# =========================
def handle_inventory(pos_item, quantity, business):

    # =========================
    # KEG PRODUCT
    # =========================
    if pos_item.keg_type:

        consume_keg(
            business=business,
            keg_type=pos_item.keg_type,
            volume=pos_item.volume_per_unit * quantity
        )

    # =========================
    # NORMAL PRODUCT
    # =========================
    else:
        product = pos_item.product

        if product:
            product.stock_quantity -= quantity
            product.save()